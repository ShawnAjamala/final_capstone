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

## API Endpoints

### Public

GET / — Public hotel dashboard

### Authentication

POST /api/auth/register/ — Register new user (guest/staff/admin)
POST /api/auth/login/ — Login, returns JWT tokens
POST /api/auth/logout/ — Logout
GET /api/auth/me/ — Current user info

### Dashboards

GET /api/guest/dashboard/ — Guest dashboard
GET /api/staff/dashboard/ — Staff dashboard (approved staff only)
GET /api/admin/dashboard/ — Admin dashboard

### Rooms

GET /api/rooms/ — List all active rooms
GET /api/rooms/available/?check_in=&check_out= — Available rooms by date range
GET /api/rooms/:id/ — Room details
POST /api/rooms/create/ — Staff creates room (with image)
PUT /api/rooms/:id/update/ — Staff updates room
DELETE /api/rooms/:id/delete/ — Staff deactivates room (soft delete)
POST /api/rooms/book/ — Guest books a room
GET /api/rooms/my-bookings/ — Guest's room bookings
POST /api/rooms/:id/cancel/ — Guest cancels booking
GET /api/rooms/all-bookings/ — Staff views all room bookings
POST /api/rooms/:id/check-in/ — Staff checks in guest
POST /api/rooms/:id/check-out/ — Staff checks out guest
DELETE /api/rooms/booking/:id/delete/ — Staff deletes booking
DELETE /api/rooms/my-booking/:id/delete/ — Guest deletes completed booking

### Restaurant Tables

GET /api/tables/ — List all active tables
GET /api/tables/available/?date=&start_time=&end_time=&guests= — Available tables by date/time
POST /api/tables/create/ — Staff creates table (with image)
PUT /api/tables/:id/update/ — Staff updates table
DELETE /api/tables/:id/delete/ — Staff deactivates table (soft delete)
POST /api/tables/reserve/ — Guest reserves a table
GET /api/tables/my-bookings/ — Guest's table reservations
POST /api/tables/:id/cancel/ — Guest cancels reservation
GET /api/tables/all-bookings/ — Staff views all reservations
POST /api/tables/:id/complete/ — Staff completes reservation
DELETE /api/tables/booking/:id/delete/ — Staff deletes reservation
DELETE /api/tables/my-booking/:id/delete/ — Guest deletes completed reservation

### Conference Rooms

GET /api/conference/ — List all active conference rooms
GET /api/conference/available/?date=&start_time=&end_time=&guests= — Available rooms by date/time
POST /api/conference/create/ — Staff creates conference room (with image)
PUT /api/conference/:id/update/ — Staff updates conference room
DELETE /api/conference/:id/delete/ — Staff deactivates conference room (soft delete)
POST /api/conference/book/ — Guest books conference room with packages
GET /api/conference/my-bookings/ — Guest's conference bookings
POST /api/conference/:id/cancel/ — Guest cancels booking
GET /api/conference/all-bookings/ — Staff views all conference bookings
POST /api/conference/:id/complete/ — Staff completes booking
DELETE /api/conference/booking/:id/delete/ — Staff deletes booking
DELETE /api/conference/my-booking/:id/delete/ — Guest deletes completed booking

### Event Venues

GET /api/venues/ — List all active venues
GET /api/venues/available/?date=&guests=&event_type= — Available venues by date
POST /api/venues/create/ — Staff creates venue (with image)
PUT /api/venues/:id/update/ — Staff updates venue
DELETE /api/venues/:id/delete/ — Staff deactivates venue (soft delete)
POST /api/venues/book/ — Guest books venue with event-type packages
GET /api/venues/my-bookings/ — Guest's venue bookings
POST /api/venues/:id/cancel/ — Guest cancels booking
GET /api/venues/all-bookings/ — Staff views all venue bookings
POST /api/venues/:id/complete/ — Staff completes booking
DELETE /api/venues/booking/:id/delete/ — Staff deletes booking
DELETE /api/venues/my-booking/:id/delete/ — Guest deletes completed booking

### M-Pesa Payments

POST /api/mpesa/pay/ — Initiate STK Push payment
POST /api/mpesa/callback/ — Safaricom payment callback
GET /api/mpesa/status/:checkout_id/ — Check payment status
POST /api/mpesa/test-pay/ — Test payment without booking

### Admin Management

GET /api/admin/users/ — List all users
GET /api/admin/guests/ — Filter guest users only
GET /api/admin/staff/ — Filter staff users only
GET /api/admin/admins/ — Filter admin users only
GET /api/admin/staff/pending/ — Staff awaiting approval
POST /api/admin/staff/approve/ — Approve staff member
POST /api/admin/staff/reject/ — Reject and delete staff
DELETE /api/admin/users/:id/delete/ — Permanently delete any user

### Profile

GET /api/profile/ — Get user profile with initials
POST /api/profile/update-password/ — Change password
DELETE /api/profile/delete-account/ — Delete own account

### Analytics

GET /api/staff/analytics/ — Staff dashboard statistics
GET /api/admin/analytics/ — Admin dashboard statistics with user counts

### Cloudinary

POST /api/upload/ — Upload image to Cloudinary
POST /api/delete-image/ — Delete image from Cloudinary

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

