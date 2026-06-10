from django.db import models

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
# UserProfile extends Django User with role and approval status.
# PASSWORDS: Guest = any | Staff = 111111 | Admin = 000000
# Staff must be approved by admin before accessing staff endpoints.

from django.contrib.auth.models import User

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


### ==================== ROOM MODELS ====================

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
    image = models.ImageField(upload_to='rooms/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['room_number']

    def __str__(self):
        return f"Room {self.room_number} - {self.room_type}"

### ==================== END OF ROOM MODELS ====================