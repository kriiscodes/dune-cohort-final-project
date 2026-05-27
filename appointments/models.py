from django.conf import settings
from django.db import models


class AvailabilityRule(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    doctor = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="availability_rules",)
    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.PositiveIntegerField(default=30)  # minutes

    def __str__(self):
        return f"{self.doctor.username}: {self.get_weekday_display()} {self.start_time}–{self.end_time}"
    
    
class Appointment(models.Model):
    class Status(models.TextChoices):
        BOOKED = "booked", "Booked"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"
        NO_SHOW = "no_show", "No-show"

    doctor = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="doctor_appointments",)
    patient = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="patient_appointments",)
    scheduled_for = models.DateTimeField()
    status = models.CharField(max_length=20,choices=Status.choices,default=Status.BOOKED,)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['doctor', 'scheduled_for'], condition=models.Q(status="booked"), name='unique_active_booking_per_slot'),
        ]
    def __str__(self):
        return f"{self.patient.username} → Dr. {self.doctor.username} @ {self.scheduled_for} ({self.status})"    