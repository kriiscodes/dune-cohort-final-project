from rest_framework import serializers
from accounts.models import DoctorProfile


class DoctorSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ["id", "name", "specialty", "bio", "fee", "photo"]