from django.contrib import admin
from .models import (
    MpesaTransaction, Room, Booking,
    RestaurantTable, TableBooking, UserProfile,
    ConferenceRoom, ConferenceBooking,
    Venue, VenueBooking,
    CancellationRequest, Refund  # Add these imports
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
    search_fields = ['guest__username', 'room__room_number']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_approved', 'must_change_password']
    list_filter = ['role', 'is_approved']

@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = ['id', 'table_number', 'capacity', 'price_per_slot', 'is_active']
    list_filter = ['is_active']

@admin.register(TableBooking)
class TableBookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest', 'table', 'reservation_date', 'start_time', 'end_time', 'status', 'payment_status']
    list_filter = ['status', 'payment_status']

@admin.register(ConferenceRoom)
class ConferenceRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'capacity', 'price_per_hour', 'is_active']
    list_filter = ['is_active']

@admin.register(ConferenceBooking)
class ConferenceBookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest', 'conference_room', 'booking_date', 'start_time', 'end_time', 'status', 'payment_status']
    list_filter = ['status', 'payment_status']

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'venue_type', 'capacity', 'price_per_day', 'is_active']
    list_filter = ['venue_type', 'is_active']

@admin.register(VenueBooking)
class VenueBookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest', 'venue', 'event_type', 'event_date', 'status', 'payment_status']
    list_filter = ['status', 'payment_status']
    search_fields = ['guest__username', 'venue__name']

# ==================== CANCELLATION REQUESTS ====================
@admin.register(CancellationRequest)
class CancellationRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest', 'booking_id', 'booking_type', 'status', 'reason_short', 'created_at', 'refund_amount']
    list_filter = ['status', 'booking_type']
    search_fields = ['guest__username', 'booking_id', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def reason_short(self, obj):
        return obj.reason[:50] + '...' if len(obj.reason) > 50 else obj.reason
    reason_short.short_description = 'Reason'
    
    actions = ['approve_requests', 'reject_requests', 'delete_selected_requests']
    
    def approve_requests(self, request, queryset):
        count = 0
        for cancellation in queryset:
            if cancellation.status == 'pending':
                cancellation.status = 'approved'
                cancellation.save()
                count += 1
        self.message_user(request, f"{count} cancellation request(s) approved.")
    approve_requests.short_description = "Approve selected cancellation requests"
    
    def reject_requests(self, request, queryset):
        count = 0
        for cancellation in queryset:
            if cancellation.status == 'pending':
                cancellation.status = 'rejected'
                cancellation.save()
                count += 1
        self.message_user(request, f"{count} cancellation request(s) rejected.")
    reject_requests.short_description = "Reject selected cancellation requests"
    
    def delete_selected_requests(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} cancellation request(s) deleted.")
    delete_selected_requests.short_description = "Delete selected cancellation requests"

# ==================== REFUNDS ====================
@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking_id', 'booking_type', 'amount', 'status', 'phone_number', 'processed_by', 'created_at']
    list_filter = ['status', 'booking_type']
    search_fields = ['booking_id', 'phone_number', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    actions = ['process_refunds', 'delete_selected_refunds']
    
    def process_refunds(self, request, queryset):
        count = 0
        for refund in queryset:
            if refund.status == 'pending':
                refund.status = 'completed'
                refund.save()
                count += 1
        self.message_user(request, f"{count} refund(s) processed.")
    process_refunds.short_description = "Process selected refunds (mark as completed)"
    
    def delete_selected_refunds(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} refund(s) deleted.")
    delete_selected_refunds.short_description = "Delete selected refunds"