from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("my-appointments/", views.my_appointments, name="my_appointments"),
    path("appointments/book/<int:doctor_id>/", views.book_appointment, name="book_appointment"),
    path("staff/", views.staff_dashboard, name="staff_dashboard"),
]