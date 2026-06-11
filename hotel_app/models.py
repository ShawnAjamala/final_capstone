from django.db import models
from django.contrib.auth.models import User

### ==================== MPESA MODELS (DO NOT TOUCH) ====================
# Stores all M-Pesa transactions for payment tracking.

class MpesaTransaction(models.Model):
    STATUS_CHOICES = [
        ("Pending",   "Pending"),
        ("Completed", "Completed"),
        ("Failed",    "Failed"),
        ("Cancelled", "Cancelled"),
    ]

    checkout_request_id = models.CharField(max_length=100, unique=True)
    phone_number        = models.CharField(max_length=15)
    amount              = models.DecimalField(max_digits=10, decimal_places=2)
    reference           = models.CharField(max_length=100)
    description         = models.CharField(max_length=255, blank=True)
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    mpesa_receipt       = models.CharField(max_length=50, blank=True, null=True)
    result_desc         = models.CharField(max_length=255, blank=True, null=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} | {self.amount} | {self.status}"

    class Meta:
        ordering = ["-created_at"]

### ==================== END OF MPESA MODELS ====================


### ==================== AUTH MODELS ====================
# Extends Django's User with role (guest/staff/admin) and approval status.
# Staff must be approved by admin before managing rooms.
# Fixed passwords stored in .env: Staff=STAFF_PASSWORD, Admin=ADMIN_PASSWORD.

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('guest', 'Guest'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='guest')
    phone = models.CharField(max_length=15, blank=True)
    is_approved = models.BooleanField(default=False)  # Staff need admin approval

    def __str__(self):
        return f"{self.user.username} - {self.role}"

### ==================== END OF AUTH MODELS ====================


### ==================== ROOM MODEL ====================
# Represents a hotel room that can be booked.
# Staff/admin create and manage rooms.
# Guests browse and book available rooms.
# is_active: False means room is hidden from listings.
# Room availability for specific dates is checked via Booking model.

class Room(models.Model):
    ROOM_TYPES = [
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite'),
        ('family', 'Family'),
    ]

    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    max_guests = models.IntegerField()
    description = models.TextField(blank=True)
    amenities = models.TextField(blank=True, help_text="WiFi, TV, AC, Minibar")
    is_active = models.BooleanField(default=True)  # Staff can toggle to hide room
    image = models.ImageField(upload_to='rooms/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['room_number']

    def __str__(self):
        return f"Room {self.room_number} - {self.room_type}"

### ==================== END OF ROOM MODEL ====================


### ==================== BOOKING MODEL ====================
# Links a guest to a room for specific dates.
# FLOW: Guest books → pending/unpaid → pays via M-Pesa → confirmed → staff checks in → staff checks out.
# Room is unavailable when status is 'confirmed' or 'checked_in'.
# Room becomes available again after 'checked_out' or 'cancelled'.

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),         # Just booked, not yet paid
        ('confirmed', 'Confirmed'),     # Paid via M-Pesa, room reserved
        ('checked_in', 'Checked In'),   # Guest has arrived
        ('checked_out', 'Checked Out'), # Guest has left, room free
        ('cancelled', 'Cancelled'),     # Booking cancelled, room free
    ]

    PAYMENT_STATUS = [
        ('unpaid', 'Unpaid'),  # Guest hasn't paid yet
        ('paid', 'Paid'),      # Payment received via M-Pesa
    ]

    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField()             # Arrival date
    check_out = models.DateField()            # Departure date
    guests = models.IntegerField(default=1)   # Number of guests staying
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # nights × price_per_night
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='unpaid')
    mpesa_transaction = models.ForeignKey(
        MpesaTransaction, on_delete=models.SET_NULL, null=True, blank=True
    )  # Links to the M-Pesa payment
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.id} - {self.guest.username} - Room {self.room.room_number}"

### ==================== END OF BOOKING MODEL ====================