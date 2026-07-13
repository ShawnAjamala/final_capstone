# hotel_app/staff_views.py

from datetime import date
from django.db.models import Sum, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import (
    Room, Booking, RestaurantTable, TableBooking, 
    ConferenceRoom, ConferenceBooking, Venue, VenueBooking,
    CancellationRequest, Refund
)
from .permissions import IsAdminOrStaff


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def staff_analytics(request):
    """
    Get staff analytics dashboard data with refund tracking
    Gross Revenue = ALL bookings with payment_status='paid' (any date)
    Refunds = ONLY bookings with payment_status='refunded'
    """
    today = date.today()
    
    # ============ ROOMS ============
    rooms_total = Room.objects.filter(is_active=True).count()
    
    # Booked today (active check-ins today)
    rooms_booked_today = Booking.objects.filter(
        status__in=['confirmed', 'checked_in', 'checked_out'],
        check_in__lte=today,
        check_out__gte=today
    ).count()
    
    # Gross revenue = ALL paid bookings (ANY date, ANY future)
    rooms_gross_revenue = Booking.objects.filter(
        status__in=['confirmed', 'checked_in', 'checked_out'],
        payment_status='paid'
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # Refunded amount = ONLY bookings with payment_status='refunded'
    rooms_refunded = Booking.objects.filter(
        payment_status='refunded'
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # Net revenue (gross - refunds)
    rooms_net_revenue = rooms_gross_revenue - rooms_refunded
    
    # ============ TABLES ============
    tables_total = RestaurantTable.objects.filter(is_active=True).count()
    
    tables_booked_today = TableBooking.objects.filter(
        status='confirmed',
        reservation_date=today
    ).count()
    
    tables_gross_revenue = TableBooking.objects.filter(
        status='confirmed',
        payment_status='paid'
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    tables_refunded = TableBooking.objects.filter(
        payment_status='refunded'
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    tables_net_revenue = tables_gross_revenue - tables_refunded
    
    # ============ CONFERENCE ============
    conference_total = ConferenceRoom.objects.filter(is_active=True).count()
    
    conference_booked_today = ConferenceBooking.objects.filter(
        status='confirmed',
        booking_date=today
    ).count()
    
    conference_gross_revenue = ConferenceBooking.objects.filter(
        status='confirmed',
        payment_status='paid'
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    conference_refunded = ConferenceBooking.objects.filter(
        payment_status='refunded'
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    conference_net_revenue = conference_gross_revenue - conference_refunded
    
    # ============ VENUES ============
    venues_total = Venue.objects.filter(is_active=True).count()
    
    venues_booked_today = VenueBooking.objects.filter(
        status='confirmed',
        event_date=today
    ).count()
    
    venues_gross_revenue = VenueBooking.objects.filter(
        status='confirmed',
        payment_status='paid'
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    venues_refunded = VenueBooking.objects.filter(
        payment_status='refunded'
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    venues_net_revenue = venues_gross_revenue - venues_refunded
    
    # ============ TOTAL REVENUE (All time) ============
    # Gross revenue = ALL paid bookings (any date)
    total_gross_revenue = (
        Booking.objects.filter(
            status__in=['confirmed', 'checked_in', 'checked_out'],
            payment_status='paid'
        ).aggregate(total=Sum('total_price'))['total'] or 0
    ) + (
        TableBooking.objects.filter(
            status='confirmed',
            payment_status='paid'
        ).aggregate(total=Sum('total_price'))['total'] or 0
    ) + (
        ConferenceBooking.objects.filter(
            status='confirmed',
            payment_status='paid'
        ).aggregate(total=Sum('total_price'))['total'] or 0
    ) + (
        VenueBooking.objects.filter(
            status='confirmed',
            payment_status='paid'
        ).aggregate(total=Sum('total_price'))['total'] or 0
    )
    
    # Total refunds = ONLY 'refunded'
    total_refunds = (
        Booking.objects.filter(payment_status='refunded').aggregate(total=Sum('total_price'))['total'] or 0
    ) + (
        TableBooking.objects.filter(payment_status='refunded').aggregate(total=Sum('total_price'))['total'] or 0
    ) + (
        ConferenceBooking.objects.filter(payment_status='refunded').aggregate(total=Sum('total_price'))['total'] or 0
    ) + (
        VenueBooking.objects.filter(payment_status='refunded').aggregate(total=Sum('total_price'))['total'] or 0
    )
    
    total_net_revenue = total_gross_revenue - total_refunds
    
    # ============ CANCELLATION REQUESTS ============
    pending_cancellations = CancellationRequest.objects.filter(status='pending').count()
    
    # ============ REFUNDS PENDING ============
    pending_refunds = Refund.objects.filter(status__in=['pending', 'processing']).count()
    
    return Response({
        'total_gross_revenue': int(total_gross_revenue),
        'total_refunds': int(total_refunds),
        'total_net_revenue': int(total_net_revenue),
        'pending_cancellations': pending_cancellations,
        'pending_refunds': pending_refunds,
        'rooms': {
            'total': rooms_total,
            'booked_today': rooms_booked_today,
            'gross_revenue': int(rooms_gross_revenue),
            'refunds': int(rooms_refunded),
            'net_revenue': int(rooms_net_revenue),
        },
        'tables': {
            'total': tables_total,
            'booked_today': tables_booked_today,
            'gross_revenue': int(tables_gross_revenue),
            'refunds': int(tables_refunded),
            'net_revenue': int(tables_net_revenue),
        },
        'conference': {
            'total': conference_total,
            'booked_today': conference_booked_today,
            'gross_revenue': int(conference_gross_revenue),
            'refunds': int(conference_refunded),
            'net_revenue': int(conference_net_revenue),
        },
        'venues': {
            'total': venues_total,
            'booked_today': venues_booked_today,
            'gross_revenue': int(venues_gross_revenue),
            'refunds': int(venues_refunded),
            'net_revenue': int(venues_net_revenue),
        },
    })