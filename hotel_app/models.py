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
### ==================== RESTAURANT TABLE MODEL ====================
# Represents a restaurant table that can be reserved.
# Staff create and manage tables. Guests browse and reserve.
# Tables are booked for a specific date + time slot.

class RestaurantTable(models.Model):
    table_number = models.CharField(max_length=10, unique=True)
    capacity = models.IntegerField()  # How many people can sit
    price_per_slot = models.DecimalField(max_digits=10, decimal_places=2)  # Price for the time slot
    location = models.CharField(max_length=50, blank=True, help_text="Indoor, Terrace, Window, etc.")
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='tables/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['table_number']

    def __str__(self):
        return f"Table {self.table_number} ({self.capacity} pax)"

### ==================== END OF RESTAURANT TABLE MODEL ====================


### ==================== TABLE BOOKING MODEL ====================
# Links a guest to a table for a specific date and time slot.
# Time slots prevent double-booking.
# FLOW: Guest reserves → pending/unpaid → pays via M-Pesa → confirmed.
# After reservation time ends, staff marks as completed → table available.

class TableBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ]

    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='table_bookings')
    table = models.ForeignKey(RestaurantTable, on_delete=models.CASCADE, related_name='bookings')
    reservation_date = models.DateField()
    start_time = models.TimeField()  # e.g., 12:00
    end_time = models.TimeField()    # e.g., 14:00
    guests = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='unpaid')
    mpesa_transaction = models.ForeignKey(MpesaTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Table #{self.id} - {self.guest.username} - Table {self.table.table_number}"
    ### ==================== CONFERENCE ROOM MODEL ====================

class ConferenceRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capacity = models.IntegerField()
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.TextField(blank=True, help_text="Projector, Whiteboard, Video Conferencing, etc.")
    additional_packages = models.TextField(blank=True, help_text="Catering: 500, Tech Support: 1000")
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='conference/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.capacity} pax)"

### ==================== END OF CONFERENCE ROOM MODEL ====================


### ==================== CONFERENCE ROOM MODEL ====================
class ConferenceRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capacity = models.IntegerField()
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.TextField(blank=True, help_text="Projector, Whiteboard, Video Conferencing, etc.")
    additional_packages = models.TextField(blank=True, help_text="Catering: 500, Tech Support: 1000")
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='conference/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.capacity} pax)"


### ==================== CONFERENCE BOOKING MODEL ====================
class ConferenceBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ]

    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conference_bookings')
    conference_room = models.ForeignKey(ConferenceRoom, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    guests = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    selected_packages = models.TextField(blank=True, help_text="JSON list of selected packages")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='unpaid')
    mpesa_transaction = models.ForeignKey(MpesaTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Conference #{self.id} - {self.guest.username} - {self.conference_room.name}"