from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import generics, status
from accounts.models import DoctorProfile
from .serializers import DoctorSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Appointment, AvailabilityRule
from .serializers import AppointmentSerializer
from .services import create_booking, get_available_slots,mark_appointment_completed, mark_appointment_no_show, cancel_appointment
from datetime import date, datetime
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseNotAllowed, Http404
from .forms import AvailabilityRuleForm


def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")


def doctor_list(request):
    q = request.GET.get("q", "").strip()

    doctors = DoctorProfile.objects.filter(is_verified=True).select_related("user")

    if q:
        from django.db.models import Q
        query = Q(user__username__icontains=q) | Q(specialty__icontains=q)
        try:
            query |= Q(fee__lte=int(q))
        except ValueError:
            pass
        doctors = doctors.filter(query)

    return render(request, "doctor_list.html", {
        "doctors": doctors,
        "filters": {"q": q},
        "filters_applied": bool(q),
    })


def doctor_detail(request, doctor_id):
    doctor = get_object_or_404(
        DoctorProfile.objects.select_related("user"),
        id=doctor_id,
        is_verified=True,
    )
    today = date.today()
    slots = get_available_slots(doctor.user, today)
    return render(request, "doctor_detail.html", {
        "doctor": doctor,
        "today": today,
        "slots": slots,
    })

def doctor_slots_partial(request, doctor_id):
    """HTMX endpoint: returns just the slots fragment for a given date."""
    doctor = get_object_or_404(
        DoctorProfile.objects.select_related("user"),
        id=doctor_id,
        is_verified=True,
    )
    date_str = request.GET.get("date")
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        target_date = date.today()

    slots = get_available_slots(doctor.user, target_date)
    return render(request, "partials/_slots.html", {
        "doctor": doctor,
        "slots": slots,
        "selected_date": target_date,
    })



# @login_required
# def my_appointments(request):
#     return HttpResponse("Your appointments will appear here.")


@login_required
def book_appointment(request, doctor_id):
    if request.method != "POST":
        return redirect("doctor_detail", doctor_id=doctor_id)

    doctor = get_object_or_404(
        DoctorProfile.objects.select_related("user"),
        id=doctor_id,
        is_verified=True,
    )

    scheduled_for_str = request.POST.get("scheduled_for", "")
    try:
        scheduled_for = datetime.strptime(scheduled_for_str, "%Y-%m-%d %H:%M")
    except ValueError:
        messages.error(request, "Invalid slot. Please pick another.")
        return redirect("doctor_detail", doctor_id=doctor_id)

    result = create_booking(
        doctor=doctor.user,
        patient=request.user,
        scheduled_for=scheduled_for,
    )

    if result["ok"]:
        messages.success(
            request,
            f"Booked with Dr. {doctor.user.username} on {scheduled_for.strftime('%a %d %b at %H:%M')}."
        )
        return redirect("dashboard")
    else:
        messages.error(request, "That slot was just taken. Please pick another.")
        return redirect("doctor_detail", doctor_id=doctor_id)

@login_required
def mark_complete_view(request, appointment_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    
    appointment = get_object_or_404(Appointment, id=appointment_id)
    try:
        mark_appointment_completed(appointment, actor=request.user)
        messages.success(request, "Appointment marked complete.")
    except PermissionDenied:
        # 404 instead of 403 — anti-enumeration, don't confirm the appointment exists.
        from django.http import Http404
        raise Http404
    except ValidationError as e:
        messages.error(request, str(e.message if hasattr(e, "message") else e))
    
    return redirect("dashboard")


@login_required
def cancel_appointment_view(request, appointment_id):
    # Ownership check via the filter — wrong user = 404. Anti-enumeration.
    appointment = get_object_or_404(
        Appointment.objects.select_related("doctor"),
        id=appointment_id,
        patient=request.user,
    )

    next_url = request.POST.get("next") or request.GET.get("next") or ""

    if request.method == "POST":
        try:
            cancel_appointment(appointment, actor=request.user)
            messages.success(request, "Appointment cancelled.")
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, "message") else e))
        return redirect(next_url or "appointments_list")

    # GET → show the confirm page
    return render(request, "cancel_appointment_confirm.html", {
        "appointment": appointment,
        "next": next_url,
    })


@login_required
def mark_no_show_view(request, appointment_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    
    appointment = get_object_or_404(Appointment, id=appointment_id)
    try:
        mark_appointment_no_show(appointment, actor=request.user)
        messages.success(request, "Appointment marked no-show.")
    except PermissionDenied:
        from django.http import Http404
        raise Http404
    except ValidationError as e:
        messages.error(request, str(e.message if hasattr(e, "message") else e))
    
    return redirect("dashboard")


def _require_doctor(request):
    """Helper: 404 if the user isn't a doctor. Same anti-enumeration pattern."""
    if request.user.role != "doctor":
        raise Http404


@login_required
def appointments_list(request):
    role = request.user.role
    now = timezone.now()

    if role == "doctor":
        qs = (
            Appointment.objects
            .filter(doctor=request.user)
            .select_related("patient")
        )
        upcoming = qs.filter(status=Appointment.Status.BOOKED, scheduled_for__gte=now).order_by("scheduled_for")
        past_due = qs.filter(status=Appointment.Status.BOOKED, scheduled_for__lt=now).order_by("-scheduled_for")
        history = qs.exclude(status=Appointment.Status.BOOKED).order_by("-scheduled_for")[:50]
        return render(request, "appointments_list.html", {
            "role": role,
            "now": now,
            "upcoming": upcoming,
            "past_due": past_due,
            "history": history,
        })

    if role == "patient":
        qs = (
            Appointment.objects
            .filter(patient=request.user)
            .select_related("doctor")
        )
        upcoming = qs.filter(status=Appointment.Status.BOOKED, scheduled_for__gte=now).order_by("scheduled_for")
        history = qs.exclude(status=Appointment.Status.BOOKED).order_by("-scheduled_for")[:50]
        past_booked = qs.filter(status=Appointment.Status.BOOKED, scheduled_for__lt=now).order_by("-scheduled_for")
        return render(request, "appointments_list.html", {
            "role": role,
            "now": now,
            "upcoming": upcoming,
            "past_booked": past_booked,
            "history": history,
        })

    # admin and any other role: 404 — they should use the Django admin
    raise Http404


@login_required
def availability_list(request):
    _require_doctor(request)
    rules = (
        AvailabilityRule.objects
        .filter(doctor=request.user)
        .order_by("weekday", "start_time")
    )
    return render(request, "availability_list.html", {"rules": rules})


@login_required
def availability_create(request):
    _require_doctor(request)

    if request.method == "POST":
        form = AvailabilityRuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.doctor = request.user   # attach owner server-side — never trust client
            rule.save()
            messages.success(request, "Availability rule added.")
            return redirect("availability_list")
    else:
        form = AvailabilityRuleForm()

    return render(request, "availability_form.html", {
        "form": form,
        "mode": "create",
    })


@login_required
def availability_edit(request, rule_id):
    _require_doctor(request)

    # Ownership check via the filter — wrong doctor = 404, not 403. Anti-enumeration.
    rule = get_object_or_404(AvailabilityRule, id=rule_id, doctor=request.user)

    if request.method == "POST":
        form = AvailabilityRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, "Availability rule updated.")
            return redirect("availability_list")
    else:
        form = AvailabilityRuleForm(instance=rule)

    return render(request, "availability_form.html", {
        "form": form,
        "mode": "edit",
        "rule": rule,
    })


@login_required
def availability_delete(request, rule_id):
    _require_doctor(request)
    rule = get_object_or_404(AvailabilityRule, id=rule_id, doctor=request.user)

    if request.method == "POST":
        rule.delete()
        messages.success(request, "Availability rule removed.")
        return redirect("availability_list")

    # GET → show the confirm page
    return render(request, "availability_confirm_delete.html", {"rule": rule})







from rest_framework import generics
from accounts.models import DoctorProfile
from .serializers import DoctorSerializer


class DoctorListAPIView(generics.ListAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorSerializer


class DoctorDetailAPIView(generics.RetrieveAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorSerializer
    lookup_url_kwarg = "doctor_id"
    
    

class AppointmentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = create_booking(doctor=serializer.validated_data["doctor"],patient=request.user,scheduled_for=serializer.validated_data["scheduled_for"],)

        
        if result["ok"]:
            output = AppointmentSerializer(result["appointment"])
            return Response(output.data, status=status.HTTP_201_CREATED)

        return Response(
            {"detail": "That slot was just taken."},status=status.HTTP_409_CONFLICT,)    


class AppointmentCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, appointment_id):
       
        appointment = Appointment.objects.filter(id=appointment_id,patient=request.user,).first()

       
        if appointment is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

      
        appointment.status = "cancelled"
        appointment.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
    

