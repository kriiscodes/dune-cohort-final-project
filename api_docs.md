# MediSlot API

Local: `http://127.0.0.1:8000` — production URL goes here once it's on Render.

Everything returns JSON. The two write endpoints need a token; grab one by POSTing
your login to `/api/auth/token/`, then send it on every authed request as a header:
`Authorization: Token <whatever-you-got-back>`.

## Doctors (public, no auth)

`GET /api/doctors/` lists them, `GET /api/doctors/<id>/` gives you one. Nothing fancy —
id, name, specialty, bio, fee, photo. A bad id on the detail route gets you a 404.

## Booking

`POST /api/appointments/` — needs a token. Send the doctor and the time:

    { "doctor": 1, "scheduled_for": "2026-06-01T10:00:00" }

You don't send who the patient is — that comes from your token, not the body (otherwise
you could book slots in other people's names). Status starts as "booked" server-side too;
the client doesn't get to set it.

Come back with a 201 and the created appointment. If that slot's already taken you get a
409 instead of the booking. Forget the token and it's a 401. Send junk in the body — missing
doctor, a nonsense datetime — and the serializer bounces it with a 400 before it ever
hits the database.

## Cancelling

`DELETE /api/appointments/<id>/`, token required. Success is a 204 with an empty body.

Worth knowing: this doesn't actually delete the row. It flips the status to "cancelled" —
the record sticks around so no-shows and cancellations can be reported on later, and the
slot frees back up for someone else. And if you try to cancel an appointment that isn't
yours, you get a 404, not a 403 — same answer as a row that doesn't exist, so nobody can
poke around guessing which appointment ids are real.