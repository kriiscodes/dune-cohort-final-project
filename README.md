# MediSlot

A doctor-appointment booking app built with Django. Doctors publish the hours
they're available, patients find a doctor and grab an open slot, and the whole
thing keeps itself honest — no double-booking the same time, no booking with a
doctor who hasn't been approved yet.

It started as my final project for the Dune Cohort, but it's a real, working
booking system rather than a toy: custom user roles, a slot engine that turns
weekly schedules into actual bookable times, a small JSON API, and admin
verification before a doctor can take patients.

## What it does

There are three kinds of people in MediSlot, and the app behaves differently for each:

- **Patients** sign up, browse the list of verified doctors, open a doctor to see
  their open slots for the week, and book one. They can see their upcoming
  appointments and cancel if plans change.
- **Doctors** set up *availability rules* — "I see patients Mondays 9–5, 30 minutes
  each" — and the app turns those into concrete slots patients can book. On their
  dashboard they see who's coming in and can mark an appointment as completed or a
  no-show after the fact.
- **Admins** approve doctors. A doctor who signs up isn't visible to patients until
  an admin verifies them, so nobody can list themselves as a physician and start
  taking bookings unchecked.

A couple of rules are enforced at the database level rather than just in the UI, so
they hold even if someone pokes at the API directly:

- The same doctor can't have two active bookings at the same time (a unique
  constraint on doctor + time while the appointment is still "booked").
- Cancelling doesn't wipe the record — it flips the status to `cancelled`. The slot
  frees up for someone else, but the history stays so cancellations and no-shows can
  be reported on later.

## The API

There's a small REST API (Django REST Framework) sitting next to the web app, so
the same data is usable from a script or a separate frontend. Doctors are public;
booking and cancelling need a token. Full details — request shapes, status codes,
the reasoning behind a few of the choices — are in [api_docs.md](api_docs.md), and
there's a Postman collection in the repo if you'd rather click than curl.

Quick taste:

```
GET    /api/doctors/                  # list doctors (public)
GET    /api/doctors/<id>/             # one doctor (public)
POST   /api/appointments/             # book a slot (token)
DELETE /api/appointments/<id>/        # cancel (token)
POST   /api/token/                    # exchange login for a token
```

## Built with

- **Django 6** + **Django REST Framework**
- **SQLite** in development, **PostgreSQL** (Supabase) in production
- **WhiteNoise** for serving static files
- **Cloudinary** for uploaded images (doctor photos), so they survive redeploys
- **Gunicorn** on **Render** for hosting

## Running it locally

You'll need Python 3.13 and git.

```bash
# 1. clone and step in
git clone https://github.com/kriiscodes/dune-cohort-final-project.git
cd dune-cohort-final-project

# 2. virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. dependencies
pip install -r requirements.txt

# 4. environment file
copy .env.example .env       # Windows  (cp on macOS/Linux)
```

Open `.env` and set a `SECRET_KEY` (any long random string) and `DEBUG=True`.
Leave `DATABASE_URL` and `CLOUDINARY_URL` blank — empty means "use local SQLite and
the local `media/` folder," which is exactly what you want for development.

```bash
# 5. set up the database and an admin login
python manage.py migrate
python manage.py createsuperuser

# 6. go
python manage.py runserver
```

Then visit http://127.0.0.1:8000. The admin lives at `/admin/`.

## Configuration

Everything environment-specific is read from `.env` (see `.env.example` for the full
list). The two that flip the app from "local" to "production" mode:

- `DATABASE_URL` — set it to a PostgreSQL URL and the app uses that; leave it blank
  and it falls back to SQLite.
- `CLOUDINARY_URL` — set it and uploads go to Cloudinary; leave it blank and they
  land in the local `media/` folder.

`DEBUG` defaults to `False`, and when it's off the app turns on the usual production
safety rails (HTTPS redirect, secure cookies, HSTS). Keep `DEBUG=True` locally so you
can actually develop over plain HTTP.

## Deployment

Production runs on Render with a Supabase Postgres database and Cloudinary for media.
The repo already includes what Render needs — a `requirements.txt`, and a `Procfile`.
On Render you point a Web Service at this repo with:

- **Build command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- **Start command:** `gunicorn config.wsgi`
- **Environment variables:**

  | Key | Example value |
  | --- | --- |
  | `SECRET_KEY` | a long random string |
  | `DEBUG` | `False` |
  | `DATABASE_URL` | your Supabase connection string |
  | `CLOUDINARY_URL` | `cloudinary://key:secret@cloud-name` |
  | `ALLOWED_HOSTS` | `medislot-abcd.onrender.com` (your Render hostname, no `https://`) |
  | `CSRF_TRUSTED_ORIGINS` | `https://medislot-abcd.onrender.com` (same host, with `https://`) |

---

Built by [Kriiscodes](https://github.com/kriiscodes) for the Dune Cohort.
