from django.contrib import admin
from .models import (
    MpesaTransaction, Room, Booking,
    RestaurantTable, TableBooking, UserProfile
)

@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'phone_number', 'amount', 'status', 'reference', 'created_at']
    list_filter = ['status']
    search_fields = ['phone_number', 'reference']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'room_number', 'room_type', 'price_per_night', 'is_active']
    list_filter = ['room_type', 'is_active']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest', 'room', 'check_in', 'check_out', 'status', 'payment_status']
    list_filter = ['status', 'payment_status']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_approved']
    list_filter = ['role', 'is_approved']

@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = ['id', 'table_number', 'capacity', 'price_per_slot', 'is_active']
    list_filter = ['is_active']

@admin.register(TableBooking)
class TableBookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest', 'table', 'reservation_date', 'start_time', 'end_time', 'status']
    list_filter = ['status', 'payment_status']