from django.contrib.auth import get_user_model
from django.db import transaction
from .models import DoctorProfile  
User = get_user_model()


def make_user_doctor(username, email, password, **profile_kwargs):
    """
    Create a User with role='doctor' AND a stub DoctorProfile in one transaction.
    Either both rows exist after this call, or neither does.
    """
    

    with transaction.atomic():
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role="doctor",
        )
        DoctorProfile.objects.create(user=user, **profile_kwargs)
        return user