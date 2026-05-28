from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from .forms import SignUpForm
from .services import make_user_doctor
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

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
    return HttpResponse(
        f"Dashboard placeholder for {request.user.username} ({request.user.role})"
    )