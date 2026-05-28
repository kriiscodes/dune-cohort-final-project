from rest_framework import serializers
from accounts.models import DoctorProfile
from .models import Appointment

class DoctorSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ["id", "name", "specialty", "bio", "fee", "photo"]
        
class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["id", "doctor", "scheduled_for", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]
        validators = [] 