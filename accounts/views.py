from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from .forms import SignUpForm
from .services import make_user_doctor
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from datetime import date,timedelta
from appointments.models import Appointment
from django.utils import timezone


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            if form.cleaned_data["register_as_doctor"]:
                user = make_user_doctor(
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password1"],
                )
            else:
                user = form.save()
            login(request, user)
            messages.success(request, "Welcome to MediSlot!")
            return redirect("dashboard")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})




@login_required
def dashboard_view(request):
    role = request.user.role
    context = {"today": date.today()}

    if role == "doctor":
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        week_end = today_start + timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        my_appointments = Appointment.objects.filter(doctor=request.user)

        today_count = my_appointments.filter(
            scheduled_for__gte=today_start,
            scheduled_for__lt=today_end,
            status=Appointment.Status.BOOKED,
        ).count()

        week_count = my_appointments.filter(
            scheduled_for__gte=today_start,
            scheduled_for__lt=week_end,
            status=Appointment.Status.BOOKED,
        ).count()

        no_show_count = my_appointments.filter(
            scheduled_for__gte=thirty_days_ago,
            status=Appointment.Status.NO_SHOW,
        ).count()

        upcoming = (
            my_appointments
            .filter(status=Appointment.Status.BOOKED)
            .select_related("patient")
            .order_by("scheduled_for")[:20]
        )

        context.update({
            "now": now,
            "today_count": today_count,
            "week_count": week_count,
            "no_show_count": no_show_count,
            "upcoming": upcoming,
        })
        return render(request, "dashboards/doctor_dashboard.html", context)

    elif role == "admin":
        return render(request, "dashboards/admin_dashboard.html", context)

    else:
        # patient
        appointments = (
            Appointment.objects
            .filter(patient=request.user)
            .select_related("doctor")
            .order_by("-scheduled_for")
        )
        context["upcoming"] = appointments.filter(status="booked")
        context["completed_count"] = appointments.filter(status="completed").count()
        context["cancelled_count"] = appointments.filter(status="cancelled").count()
        return render(request, "dashboards/patient_dashboard.html", context)