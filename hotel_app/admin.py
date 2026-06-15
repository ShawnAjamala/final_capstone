from django.contrib import admin
from .models import (
    MpesaTransaction, Room, Booking,
    RestaurantTable, TableBooking, UserProfile,
    ConferenceRoom, ConferenceBooking
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

@admin.register(ConferenceRoom)
class ConferenceRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'capacity', 'price_per_hour', 'is_active']
    list_filter = ['is_active']

@admin.register(ConferenceBooking)
class ConferenceBookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest', 'conference_room', 'booking_date', 'start_time', 'end_time', 'status']
    list_filter = ['status', 'payment_status']

from .models import Venue, VenueBooking
@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'venue_type', 'capacity', 'price_per_day', 'is_active']

@admin.register(VenueBooking)
class VenueBookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest', 'venue', 'event_type', 'event_date', 'status']