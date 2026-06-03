from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, DoctorProfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    register_as_doctor = forms.BooleanField(required=False,label="I'm a doctor (subject to verification)",)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")


class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        # is_verified is admin-only — never expose it as an editable field.
        fields = ("specialty", "bio", "fee", "photo")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }