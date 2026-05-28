from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import generics
from accounts.models import DoctorProfile
from .serializers import DoctorSerializer



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


from rest_framework import generics
from accounts.models import DoctorProfile
from .serializers import DoctorSerializer


class DoctorListAPIView(generics.ListAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorSerializer


class DoctorDetailAPIView(generics.RetrieveAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorSerializer
    lookup_url_kwarg = "doctor_id"
    
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Appointment
from .serializers import AppointmentSerializer
from .services import create_booking


class AppointmentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = create_booking(doctor=serializer.validated_data["doctor"],patient=request.user,scheduled_for=serializer.validated_data["scheduled_for"],)

        
        if result["ok"]:
            output = AppointmentSerializer(result["appointment"])
            return Response(output.data, status=status.HTTP_201_CREATED)

        return Response(
            {"detail": "That slot was just taken."},status=status.HTTP_409_CONFLICT,)    


class AppointmentCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, appointment_id):
       
        appointment = Appointment.objects.filter(id=appointment_id,patient=request.user,).first()

       
        if appointment is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

      
        appointment.status = "cancelled"
        appointment.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
    

