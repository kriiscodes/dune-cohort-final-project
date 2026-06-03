from datetime import datetime, timedelta
from django.utils import timezone
from django.db import IntegrityError
from appointments.models import AvailabilityRule, Appointment
from django.core.exceptions import PermissionDenied, ValidationError


# def get_available_slots(doctor, date):
#     rules = AvailabilityRule.objects.filter(doctor=doctor,weekday=date.weekday())
#     taken = Appointment.objects.filter(doctor=doctor,status="booked",scheduled_for__date=date,)
#     taken_times = {appt.scheduled_for for appt in taken} 
#     slots = []
#     for rule in rules:
#         cursor = timezone.make_aware(datetime.combine(date, rule.start_time))
#         closing = timezone.make_aware(datetime.combine(date, rule.end_time))
#         duration = timedelta(minutes=rule.slot_duration)

#         while cursor + duration <= closing:
#             if cursor not in taken_times:
#                 slots.append(cursor)
#             cursor += duration
#     return slots



def create_booking(doctor, patient, scheduled_for):
    if patient.role != "patient":
        raise ValidationError("Only patients can book appointments.")
    already_booked = Appointment.objects.filter(doctor=doctor,scheduled_for=scheduled_for,status="booked",).exists()
    if already_booked:
        return {"ok": False, "reason": "slot_taken", "appointment": None}
    try:
        appointment = Appointment.objects.create(doctor=doctor,patient=patient,scheduled_for=scheduled_for,status="booked", )
    except IntegrityError:
        return {"ok": False, "reason": "slot_taken", "appointment": None}
    return {"ok": True, "reason": None, "appointment": appointment}





def get_available_slots(doctor_user, target_date):
    """
    For a given doctor (User) on a given date, return the list of bookable
    datetime slots: generated from availability rules, minus existing bookings.
    """
    weekday = target_date.weekday()  # Monday=0 ... Sunday=6

    rules = AvailabilityRule.objects.filter(doctor=doctor_user, weekday=weekday)
    if not rules.exists():
        return []

    candidate_slots = []
    for rule in rules:
        slot_start = datetime.combine(target_date, rule.start_time)
        end = datetime.combine(target_date, rule.end_time)
        duration = timedelta(minutes=rule.slot_duration)

        while slot_start + duration <= end:
            candidate_slots.append(slot_start)
            slot_start += duration

    booked_datetimes = set(
        Appointment.objects
        .filter(doctor=doctor_user, scheduled_for__date=target_date, status="booked")
        .values_list("scheduled_for", flat=True)
    )

    available = [slot for slot in candidate_slots if slot not in booked_datetimes]
    return available

def mark_appointment_completed(appointment, actor):
    """
    Transition: booked -> completed.
    
    Only the doctor on the appointment can do this.
    Only past appointments can be marked completed (can't complete the future).
    Only 'booked' appointments are eligible (can't re-complete or revive cancelled ones).
    """
    # 1. Ownership check — anti-enumeration, same pattern as the DELETE endpoint.
    if appointment.doctor != actor:
        raise PermissionDenied("You can't modify another doctor's appointment.")
    
    # 2. State machine check — illegal transitions blocked at the service layer.
    if appointment.status != Appointment.Status.BOOKED:
        raise ValidationError(
            f"Can't mark complete: appointment is {appointment.status}, not booked."
        )
    # 3. Time check — can't complete an appointment that hasn't happened yet.
    if appointment.scheduled_for > timezone.now():
        raise ValidationError("Can't mark complete: appointment is still in the future.")
    
    appointment.status = Appointment.Status.COMPLETED
    appointment.save(update_fields=["status"])
    return appointment

def mark_appointment_no_show(appointment, actor):
    """
    Transition: booked -> no_show.
    
    Same guards as mark_completed. The semantic difference is the whole point of
    the product: a no-show is *not* a cancellation — the patient just didn't turn up.
    Tracked separately so we can report on it.
    """
    if appointment.doctor != actor:
        raise PermissionDenied("You can't modify another doctor's appointment.")
    
    if appointment.status != Appointment.Status.BOOKED:
        raise ValidationError(
            f"Can't mark no-show: appointment is {appointment.status}, not booked."
        )
    
    if appointment.scheduled_for > timezone.now():
        raise ValidationError("Can't mark no-show: appointment is still in the future.")
    
    appointment.status = Appointment.Status.NO_SHOW
    appointment.save(update_fields=["status"])
    return appointment


def cancel_appointment(appointment, actor):
    """
    Transition: booked -> cancelled.

    Only the patient who booked the appointment can cancel it (the doctor uses
    no-show / complete for post-visit close-out — distinct semantics).
    Only future appointments can be cancelled — once the slot has passed,
    the doctor needs to mark complete or no-show instead.
    """
    if appointment.patient != actor:
        raise PermissionDenied("You can't cancel another patient's appointment.")

    if appointment.status != Appointment.Status.BOOKED:
        raise ValidationError(
            f"Can't cancel: appointment is {appointment.status}, not booked."
        )

    if appointment.scheduled_for <= timezone.now():
        raise ValidationError("Can't cancel an appointment that's already started or passed.")

    appointment.status = Appointment.Status.CANCELLED
    appointment.save(update_fields=["status"])
    return appointment