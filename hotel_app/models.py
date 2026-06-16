from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

### ==================== MPESA MODELS (DO NOT TOUCH) ====================

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

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('guest', 'Guest'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='guest')
    phone = models.CharField(max_length=15, blank=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

### ==================== END OF AUTH MODELS ====================


### ==================== ROOM MODEL ====================

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
    is_active = models.BooleanField(default=True)
    image = CloudinaryField('image', folder='hotel/rooms/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['room_number']

    def __str__(self):
        return f"Room {self.room_number} - {self.room_type}"


### ==================== BOOKING MODEL ====================

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ]

    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='unpaid')
    mpesa_transaction = models.ForeignKey(MpesaTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.id} - {self.guest.username} - Room {self.room.room_number}"


### ==================== RESTAURANT TABLE MODEL ====================

class RestaurantTable(models.Model):
    table_number = models.CharField(max_length=10, unique=True)
    capacity = models.IntegerField()
    price_per_slot = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=50, blank=True, help_text="Indoor, Terrace, Window, etc.")
    is_active = models.BooleanField(default=True)
    image = CloudinaryField('image', folder='hotel/tables/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['table_number']

    def __str__(self):
        return f"Table {self.table_number} ({self.capacity} pax)"


### ==================== TABLE BOOKING MODEL ====================

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
    start_time = models.TimeField()
    end_time = models.TimeField()
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
    image = CloudinaryField('image', folder='hotel/conference/', blank=True, null=True)
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


### ==================== VENUE MODEL ====================

class Venue(models.Model):
    VENUE_TYPES = [
        ('wedding', 'Wedding'),
        ('birthday', 'Birthday'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100, unique=True)
    venue_type = models.CharField(max_length=20, choices=VENUE_TYPES)
    capacity = models.IntegerField()
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    additional_packages = models.TextField(blank=True, help_text="Wedding Decor: 1, Cake: 1 | Birthday Decor: 1, Cake: 1 | Other Decor: 1")
    is_active = models.BooleanField(default=True)
    image = CloudinaryField('image', folder='hotel/venues/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.venue_type}"


### ==================== VENUE BOOKING MODEL ====================

class VenueBooking(models.Model):
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

    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='venue_bookings')
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='bookings')
    event_type = models.CharField(max_length=20, choices=[('wedding', 'Wedding'), ('birthday', 'Birthday'), ('other', 'Other')])
    event_date = models.DateField()
    guests = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    selected_packages = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='unpaid')
    mpesa_transaction = models.ForeignKey(MpesaTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Venue #{self.id} - {self.guest.username} - {self.venue.name}"