from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    return render(request, "home.html")


@login_required
def my_appointments(request):
    return HttpResponse("Your appointments will appear here.")


@login_required
def book_appointment(request, doctor_id):
    return HttpResponse(f"Booking flow for doctor #{doctor_id}.")


@staff_member_required
def staff_dashboard(request):
    return HttpResponse("Staff dashboard.")