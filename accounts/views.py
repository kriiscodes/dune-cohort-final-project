from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.shortcuts import get_object_or_404, redirect, render
from .forms import SignUpForm, UserProfileForm, DoctorProfileForm
from .models import DoctorProfile
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


def _get_doctor_profile(user):
    """Return the user's DoctorProfile if they're a doctor, else None.
    Auto-creates the profile row if a doctor somehow doesn't have one yet
    (e.g. promoted via admin without going through make_user_doctor)."""
    if user.role != "doctor":
        return None
    profile, _ = DoctorProfile.objects.get_or_create(
        user=user,
        defaults={"specialty": ""},
    )
    return profile


@login_required
def profile_view(request):
    doctor_profile = _get_doctor_profile(request.user)
    return render(request, "accounts/profile.html", {
        "doctor_profile": doctor_profile,
    })


@login_required
def profile_edit(request):
    doctor_profile = _get_doctor_profile(request.user)

    if request.method == "POST":
        user_form = UserProfileForm(request.POST, instance=request.user)
        doctor_form = (
            DoctorProfileForm(request.POST, request.FILES, instance=doctor_profile)
            if doctor_profile is not None else None
        )

        user_ok = user_form.is_valid()
        doctor_ok = doctor_form.is_valid() if doctor_form else True

        if user_ok and doctor_ok:
            user_form.save()
            if doctor_form:
                doctor_form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
    else:
        user_form = UserProfileForm(instance=request.user)
        doctor_form = (
            DoctorProfileForm(instance=doctor_profile)
            if doctor_profile is not None else None
        )

    return render(request, "accounts/profile_edit.html", {
        "user_form": user_form,
        "doctor_form": doctor_form,
        "doctor_profile": doctor_profile,
    })


@staff_member_required
def doctor_verification(request):
    """Staff-only screen for verifying doctor profiles.

    A doctor signs up with is_verified=False and stays hidden from patient
    search until a staff member approves them here. This is the only place
    in the app gated on is_staff (the rest of the role gating is via the
    custom .role field) — so deliberately uses @staff_member_required to
    distinguish "staff" from "users with role=admin".
    """
    if request.method == "POST":
        action = request.POST.get("action")
        profile_id = request.POST.get("profile_id")
        profile = get_object_or_404(DoctorProfile, id=profile_id)

        if action == "verify":
            profile.is_verified = True
            profile.save(update_fields=["is_verified"])
            messages.success(request, f"Dr. {profile.user.username} verified.")
        elif action == "unverify":
            profile.is_verified = False
            profile.save(update_fields=["is_verified"])
            messages.success(request, f"Dr. {profile.user.username} verification revoked.")
        return redirect("doctor_verification")

    pending = DoctorProfile.objects.filter(is_verified=False).select_related("user").order_by("user__username")
    verified = DoctorProfile.objects.filter(is_verified=True).select_related("user").order_by("user__username")
    return render(request, "accounts/doctor_verification.html", {
        "pending": pending,
        "verified": verified,
    })