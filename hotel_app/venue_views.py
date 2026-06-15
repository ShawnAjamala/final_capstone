from datetime import datetime
from decimal import Decimal
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Venue, VenueBooking
from .permissions import IsGuest, IsAdminOrStaff


def get_request_data(request):
    if hasattr(request, 'data') and request.data:
        return request.data
    return request.POST


### ==================== LIST ALL VENUES ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def venue_list(request):
    venues = Venue.objects.filter(is_active=True).values()
    return Response(venues)


### ==================== CHECK AVAILABILITY ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def venue_available(request):
    event_date = request.GET.get('date')
    if not event_date:
        return Response({'error': 'date required'}, status=status.HTTP_400_BAD_REQUEST)

    booked_ids = VenueBooking.objects.filter(
        status='confirmed', event_date=event_date
    ).values_list('venue_id', flat=True)

    available = Venue.objects.filter(is_active=True).exclude(id__in=booked_ids).values()
    return Response({'date': event_date, 'available_venues': list(available)})


### ==================== STAFF/ADMIN: ADD VENUE ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def venue_create(request):
    data = get_request_data(request)
    name = data.get('name')
    venue_type = data.get('venue_type')
    capacity = data.get('capacity')
    price_per_day = data.get('price_per_day')

    if not all([name, venue_type, capacity, price_per_day]):
        return Response({'error': 'name, venue_type, capacity, price_per_day required'}, status=status.HTTP_400_BAD_REQUEST)

    if Venue.objects.filter(name=name).exists():
        return Response({'error': 'Venue name already exists'}, status=status.HTTP_400_BAD_REQUEST)

    venue = Venue.objects.create(
        name=name, venue_type=venue_type, capacity=capacity,
        price_per_day=price_per_day, description=data.get('description', ''),
        additional_packages=data.get('additional_packages', ''),
        image=request.FILES.get('image') if hasattr(request, 'FILES') else None,
    )
    return Response({'message': 'Venue created', 'venue_id': venue.id, 'name': venue.name}, status=status.HTTP_201_CREATED)


### ==================== STAFF/ADMIN: EDIT VENUE ====================
@api_view(['PUT', 'POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def venue_update(request, venue_id):
    try:
        venue = Venue.objects.get(id=venue_id)
    except Venue.DoesNotExist:
        return Response({'error': 'Venue not found'}, status=status.HTTP_404_NOT_FOUND)

    data = get_request_data(request)
    venue.name = data.get('name', venue.name)
    venue.venue_type = data.get('venue_type', venue.venue_type)
    venue.capacity = data.get('capacity', venue.capacity)
    venue.price_per_day = data.get('price_per_day', venue.price_per_day)
    venue.description = data.get('description', venue.description)
    venue.additional_packages = data.get('additional_packages', venue.additional_packages)
    venue.is_active = data.get('is_active', venue.is_active)
    if hasattr(request, 'FILES') and 'image' in request.FILES:
        venue.image = request.FILES['image']
    venue.save()
    return Response({'message': 'Venue updated'})


### ==================== STAFF/ADMIN: DELETE VENUE ====================
@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def venue_delete(request, venue_id):
    try:
        venue = Venue.objects.get(id=venue_id)
        venue.is_active = False
        venue.save()
        return Response({'message': 'Venue deactivated'})
    except Venue.DoesNotExist:
        return Response({'error': 'Venue not found'}, status=status.HTTP_404_NOT_FOUND)


### ==================== GUEST: BOOK VENUE ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsGuest])
def venue_book(request):
    data = get_request_data(request)
    venue_id = data.get('venue_id')
    event_type = data.get('event_type')
    event_date = data.get('date')
    guests = data.get('guests', 1)
    selected_packages = data.get('selected_packages', [])

    if not all([venue_id, event_type, event_date]):
        return Response({'error': 'venue_id, event_type, date required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        venue = Venue.objects.get(id=venue_id, is_active=True)
    except Venue.DoesNotExist:
        return Response({'error': 'Venue not found'}, status=status.HTTP_404_NOT_FOUND)

    conflicting = VenueBooking.objects.filter(
        venue=venue, status='confirmed', event_date=event_date
    )
    if conflicting.exists():
        return Response({'error': 'Venue not available for this date'}, status=status.HTTP_400_BAD_REQUEST)

    base_price = venue.price_per_day

    # Parse packages for this event type
    # Format: "Wedding Decor: 1, Cake: 1 | Birthday Decor: 1, Cake: 1 | Other Decor: 1"
    package_prices = {}
    if venue.additional_packages:
        sections = venue.additional_packages.split('|')
        for section in sections:
            section = section.strip()
            if section.lower().startswith(event_type.lower()):
                # Extract packages after the event type prefix
                parts = section.split(' ', 1)
                if len(parts) > 1:
                    for pkg in parts[1].split(','):
                        pkg = pkg.strip()
                        if ':' in pkg:
                            name, price = pkg.split(':')
                            package_prices[name.strip()] = Decimal(price.strip())

    extra_charges = Decimal('0')
    for selected in selected_packages:
        if selected in package_prices:
            extra_charges += package_prices[selected]

    total_price = base_price + extra_charges

    booking = VenueBooking.objects.create(
        guest=request.user, venue=venue, event_type=event_type,
        event_date=event_date, guests=guests, total_price=total_price,
        selected_packages=str(selected_packages),
        status='pending', payment_status='unpaid'
    )

    return Response({
        'message': 'Venue booked. Pay via M-Pesa to confirm.',
        'booking': {
            'id': booking.id, 'venue': venue.name, 'event_type': event_type,
            'date': event_date, 'guests': guests,
            'base_price': str(base_price), 'selected_packages': selected_packages,
            'extra_charges': str(extra_charges), 'total_price': str(total_price),
            'status': booking.status,
            'next_step': f'POST /api/mpesa/pay/ with booking_id: VEN-{booking.id}'
        }
    }, status=status.HTTP_201_CREATED)


### ==================== GUEST: MY VENUE BOOKINGS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsGuest])
def my_venue_bookings(request):
    bookings = VenueBooking.objects.filter(guest=request.user).order_by('-created_at')
    data = []
    for b in bookings:
        data.append({
            'id': b.id, 'venue': b.venue.name, 'event_type': b.event_type,
            'date': b.event_date, 'guests': b.guests, 'packages': b.selected_packages,
            'total_price': str(b.total_price), 'status': b.status, 'payment_status': b.payment_status,
        })
    return Response({'bookings': data})


### ==================== GUEST: CANCEL VENUE BOOKING ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsGuest])
def cancel_venue_booking(request, booking_id):
    try:
        booking = VenueBooking.objects.get(id=booking_id, guest=request.user)
    except VenueBooking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    if booking.status == 'completed':
        return Response({'error': 'Cannot cancel completed booking'}, status=status.HTTP_400_BAD_REQUEST)
    booking.status = 'cancelled'
    booking.save()
    return Response({'message': 'Booking cancelled'})


### ==================== GUEST: DELETE MY VENUE BOOKING ====================
@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated, IsGuest])
def delete_my_venue_booking(request, booking_id):
    try:
        booking = VenueBooking.objects.get(id=booking_id, guest=request.user)
    except VenueBooking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    if booking.status not in ['completed', 'cancelled']:
        return Response({'error': 'Can only delete completed or cancelled bookings'}, status=status.HTTP_400_BAD_REQUEST)
    booking.delete()
    return Response({'message': 'Booking deleted'})


### ==================== STAFF/ADMIN: ALL VENUE BOOKINGS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def all_venue_bookings(request):
    bookings = VenueBooking.objects.all().order_by('-created_at')
    data = []
    for b in bookings:
        data.append({
            'id': b.id, 'guest': b.guest.username, 'venue': b.venue.name,
            'event_type': b.event_type, 'date': b.event_date, 'guests': b.guests,
            'packages': b.selected_packages, 'total_price': str(b.total_price),
            'status': b.status, 'payment_status': b.payment_status,
        })
    return Response({'bookings': data})


### ==================== STAFF/ADMIN: COMPLETE VENUE BOOKING ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def complete_venue_booking(request, booking_id):
    try:
        booking = VenueBooking.objects.get(id=booking_id)
    except VenueBooking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    if booking.status != 'confirmed':
        return Response({'error': 'Booking must be confirmed first'}, status=status.HTTP_400_BAD_REQUEST)
    booking.status = 'completed'
    booking.save()
    return Response({'message': f'Venue {booking.venue.name} is now available.'})


### ==================== STAFF/ADMIN: DELETE VENUE BOOKING ====================
@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def delete_venue_booking(request, booking_id):
    try:
        booking = VenueBooking.objects.get(id=booking_id)
    except VenueBooking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    if booking.status in ['pending', 'confirmed']:
        return Response({'error': 'Cannot delete active booking'}, status=status.HTTP_400_BAD_REQUEST)
    booking.delete()
    return Response({'message': 'Venue booking deleted'})