# hotel_app/staff_views.py

from datetime import date
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Room, Booking, RestaurantTable, TableBooking, ConferenceRoom, ConferenceBooking, Venue, VenueBooking
from .permissions import IsAdminOrStaff


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def staff_analytics(request):
    """
    Get staff analytics dashboard data
    Returns counts and revenue for all resources
    """
    today = date.today()
    
    # ============ ROOMS ============
    rooms_total = Room.objects.filter(is_active=True).count()
    
    rooms_booked_today = Booking.objects.filter(
        status__in=['confirmed', 'checked_in'],
        check_in__lte=today,
        check_out__gte=today
    ).count()
    
    rooms_revenue = Booking.objects.filter(
        status__in=['confirmed', 'checked_in', 'checked_out'],
        check_in__lte=today,
        check_out__gte=today
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # ============ TABLES ============
    tables_total = RestaurantTable.objects.filter(is_active=True).count()
    
    tables_booked_today = TableBooking.objects.filter(
        status='confirmed',
        reservation_date=today
    ).count()
    
    tables_revenue = TableBooking.objects.filter(
        status='confirmed',
        reservation_date=today
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # ============ CONFERENCE ============
    conference_total = ConferenceRoom.objects.filter(is_active=True).count()
    
    conference_booked_today = ConferenceBooking.objects.filter(
        status='confirmed',
        booking_date=today
    ).count()
    
    conference_revenue = ConferenceBooking.objects.filter(
        status='confirmed',
        booking_date=today
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # ============ VENUES ============
    venues_total = Venue.objects.filter(is_active=True).count()
    
    venues_booked_today = VenueBooking.objects.filter(
        status='confirmed',
        event_date=today
    ).count()
    
    venues_revenue = VenueBooking.objects.filter(
        status='confirmed',
        event_date=today
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # ============ TOTAL REVENUE (All time) ============
    total_revenue = (
        Booking.objects.filter(status__in=['confirmed', 'checked_in', 'checked_out']).aggregate(total=Sum('total_price'))['total'] or 0
    ) + (
        TableBooking.objects.filter(status='confirmed').aggregate(total=Sum('total_price'))['total'] or 0
    ) + (
        ConferenceBooking.objects.filter(status='confirmed').aggregate(total=Sum('total_price'))['total'] or 0
    ) + (
        VenueBooking.objects.filter(status='confirmed').aggregate(total=Sum('total_price'))['total'] or 0
    )
    
    return Response({
        'total_revenue': int(total_revenue),
        'rooms': {
            'total': rooms_total,
            'booked_today': rooms_booked_today,
            'revenue': int(rooms_revenue),
        },
        'tables': {
            'total': tables_total,
            'booked_today': tables_booked_today,
            'revenue': int(tables_revenue),
        },
        'conference': {
            'total': conference_total,
            'booked_today': conference_booked_today,
            'revenue': int(conference_revenue),
        },
        'venues': {
            'total': venues_total,
            'booked_today': venues_booked_today,
            'revenue': int(venues_revenue),
        },
    })