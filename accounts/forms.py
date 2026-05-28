from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    register_as_doctor = forms.BooleanField(required=False,label="I'm a doctor (subject to verification)",)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")