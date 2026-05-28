from datetime import datetime, timedelta
from django.utils import timezone
from django.db import IntegrityError
from appointments.models import AvailabilityRule, Appointment


def get_available_slots(doctor, date):
    rules = AvailabilityRule.objects.filter(doctor=doctor,weekday=date.weekday())
    taken = Appointment.objects.filter(doctor=doctor,status="booked",scheduled_for__date=date,)
    taken_times = {appt.scheduled_for for appt in taken} 
    slots = []
    for rule in rules:
        cursor = timezone.make_aware(datetime.combine(date, rule.start_time))
        closing = timezone.make_aware(datetime.combine(date, rule.end_time))
        duration = timedelta(minutes=rule.slot_duration)

        while cursor + duration <= closing:
            if cursor not in taken_times:
                slots.append(cursor)
            cursor += duration
    return slots



def create_booking(doctor, patient, scheduled_for):
    already_booked = Appointment.objects.filter(doctor=doctor,scheduled_for=scheduled_for,status="booked",).exists()
    if already_booked:
        return {"ok": False, "reason": "slot_taken", "appointment": None}
    try:
        appointment = Appointment.objects.create(doctor=doctor,patient=patient,scheduled_for=scheduled_for,status="booked", )
    except IntegrityError:
        return {"ok": False, "reason": "slot_taken", "appointment": None}
    return {"ok": True, "reason": None, "appointment": appointment}