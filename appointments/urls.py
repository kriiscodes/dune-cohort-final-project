from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path("api/token/", obtain_auth_token, name="api_token"),
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("doctors/", views.doctor_list, name="doctor_list"),
    path("doctors/<int:doctor_id>/", views.doctor_detail, name="doctor_detail"),
    path("doctors/<int:doctor_id>/slots/", views.doctor_slots_partial, name="doctor_slots_partial"),
    path("appointments/<int:appointment_id>/complete/", views.mark_complete_view, name="mark_complete"),
    path("appointments/<int:appointment_id>/no-show/", views.mark_no_show_view, name="mark_no_show"),
    path("dashboard/availability/", views.availability_list, name="availability_list"),
    path("dashboard/availability/new/", views.availability_create, name="availability_create"),
    path("dashboard/availability/<int:rule_id>/edit/", views.availability_edit, name="availability_edit"),
    path("dashboard/availability/<int:rule_id>/delete/", views.availability_delete, name="availability_delete"),
    # path("my-appointments/", views.my_appointments, name="my_appointments"),
    path("appointments/book/<int:doctor_id>/", views.book_appointment, name="book_appointment"),
    # path("staff/", views.staff_dashboard, name="staff_dashboard"),
    path("api/doctors/", views.DoctorListAPIView.as_view(), name="api_doctor_list"),
    path("api/doctors/<int:doctor_id>/", views.DoctorDetailAPIView.as_view(), name="api_doctor_detail"),
    path("api/appointments/", views.AppointmentCreateAPIView.as_view(), name="api_appointment_create"),
    path("api/appointments/<int:appointment_id>/", views.AppointmentCancelAPIView.as_view(), name="api_appointment_cancel"),
]