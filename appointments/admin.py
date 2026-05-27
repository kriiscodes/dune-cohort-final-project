from django.contrib import admin
from .models import AvailabilityRule, Appointment


admin.site.register(AvailabilityRule)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "scheduled_for", "status", "created_at")
    list_filter = ("status", "doctor")
    search_fields = ("patient__username", "doctor__username")
# Register your models here.

