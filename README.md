# Grand Horizon Hotel - Backend API

Django REST Framework backend for a complete hotel management system with M-Pesa payment integration.

**Live API:** https://final-capstone-2puq.onrender.com

**GitHub:** https://github.com/ShawnAjamala/final_capstone

---

## Overview

This backend powers the Grand Horizon Hotel platform — a full-featured hotel management API supporting room booking, restaurant table reservations, conference room booking, event venue management, and M-Pesa mobile payments.

### Core Modules

- Authentication — JWT-based auth with 3 roles (Guest, Staff, Admin)
- Room Booking — Browse, book, pay, check-in/out
- Restaurant Tables — Browse, reserve, pay, complete
- Conference Rooms — Browse, book with packages, pay, complete
- Event Venues — Browse, book by event type, pay, complete
- M-Pesa Integration — STK Push, callback processing, auto-confirmation
- Admin Management — User management, staff approval, analytics
- Profile — View profile, change password, delete account

---

## Tech Stack

- Django 5.x
- Django REST Framework
- SimpleJWT — JWT authentication
- Cloudinary — Image hosting
- PostgreSQL — Production database
- SQLite — Development database
- Daraja API — Safaricom M-Pesa integration
- Gunicorn — Production server
- django-cors-headers — CORS handling
- python-decouple — Environment variables

---

## Project Structure
final_capstone/
├── hotel_project/
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
├── hotel_app/
│ ├── models.py
│ ├── views.py
│ ├── auth_views.py
│ ├── admin_views.py
│ ├── room_views.py
│ ├── table_views.py
│ ├── conference_views.py
│ ├── venue_views.py
│ ├── analytics_views.py
│ ├── profile_views.py
│ ├── cloudinary_views.py
│ ├── serializers.py
│ ├── permissions.py
│ ├── mpesa.py
│ ├── urls.py
│ └── mpesa_urls.py
├── media/
├── static/
├── requirements.txt
├── manage.py
└── README.md

---

## Setup & Installation

### Prerequisites

- Python 3.12+
- Cloudinary account
- Safaricom Daraja developer account
- PostgreSQL (for production)

### Backend Setup
git clone https://github.com/ShawnAjamala/final_capstone.git
cd final_capstone

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

### Environment Variables (.env)
SECRET_KEY=your-secret-key
DEBUG=True

MPESA_CONSUMER_KEY=your-consumer-key
MPESA_CONSUMER_SECRET=your-consumer-secret
MPESA_PASSKEY=your-passkey
MPESA_SHORTCODE=174379
MPESA_CALLBACK_URL=https://your-domain.com/api/mpesa/callback/

CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret


---


## Authentication Flow

1. User registers with username, email, password, and role
2. Guests are auto-approved and can immediately browse and book
3. Staff accounts require admin approval before accessing management endpoints
4. Admin accounts use a fixed password stored in environment variables
5. JWT access tokens (24h) and refresh tokens (7 days) returned on login/register
6. All protected endpoints require Authorization: Bearer header

---

## Staff Approval System

1. Staff registers via /api/auth/register/ with role "staff"
2. Account created with is_approved = false
3. Staff can login but cannot access staff endpoints
4. Admin views pending staff at /api/admin/staff/pending/
5. Admin approves staff at /api/admin/staff/approve/
6. Staff can now create, edit, and manage resources

---

## M-Pesa Payment Flow

1. Guest books a resource — booking created with status "pending"
2. Guest sends payment with booking ID to /api/mpesa/pay/
3. Reference auto-formatted based on booking type prefix
4. STK Push sent to customer's phone via Safaricom Daraja API
5. Customer enters M-Pesa PIN on their phone
6. Safaricom sends callback to /api/mpesa/callback/
7. System processes the callback:
   - Updates MpesaTransaction status to "Completed"
   - Extracts booking reference prefix
   - Auto-confirms the corresponding booking
8. Booking types identified by reference prefix:
   - BK-{id} = Room booking
   - TBL-{id} = Table reservation
   - CONF-{id} = Conference booking
   - VEN-{id} = Venue booking

---

## Image Management

All images are uploaded to Cloudinary with organized folder structure:

- hotel/rooms/ — Room images
- hotel/tables/ — Table images
- hotel/conference/ — Conference room images
- hotel/venues/ — Venue images

Images are stored on Cloudinary CDN and survive server redeploys.

---

## Deployment (Render)

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect to GitHub repository
4. Build command: pip install -r requirements.txt && python manage.py migrate
5. Start command: gunicorn hotel_project.wsgi:application
6. Add all environment variables in Render dashboard
7. Deploy

---

## Known Issues

- M-Pesa Sandbox: Safaricom sandbox is unreliable for callbacks. Manual confirmation available as workaround for testing.
- Django Admin + Python 3.14: Compatibility issue with Django admin templates. Use Python 3.12 for production deployments.

---

## Author

Shawn Ajamala

