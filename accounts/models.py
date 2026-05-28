from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        PATIENT = 'patient', 'Patient'
        DOCTOR = 'doctor', 'Doctor'
        ADMIN = 'admin', 'Admin'
        
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PATIENT)

    def __str__(self):
        return f"{self.username} ({self.role})"
    

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.CharField(max_length=255)
    bio = models.TextField(blank=True)
    fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    photo = models.ImageField(upload_to = 'doctors_photos/', blank = True, null = True)
    is_verified = models.BooleanField(default=False,help_text="Admin-approved; unverified doctors are hidden from patients.",)

    def __str__(self):
        return f"{self.user.username} - {self.specialty}"
    
    
    
# Create your models here.
