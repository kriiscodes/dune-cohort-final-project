from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path("api/token/", obtain_auth_token, name="api_token"),
    path("", views.home, name="home"),
    path("my-appointments/", views.my_appointments, name="my_appointments"),
    path("appointments/book/<int:doctor_id>/", views.book_appointment, name="book_appointment"),
    path("staff/", views.staff_dashboard, name="staff_dashboard"),
    path("api/doctors/", views.DoctorListAPIView.as_view(), name="api_doctor_list"),
    path("api/doctors/<int:doctor_id>/", views.DoctorDetailAPIView.as_view(), name="api_doctor_detail"),
    path("api/appointments/", views.AppointmentCreateAPIView.as_view(), name="api_appointment_create"),
    path("api/appointments/<int:appointment_id>/", views.AppointmentCancelAPIView.as_view(), name="api_appointment_cancel"),
]