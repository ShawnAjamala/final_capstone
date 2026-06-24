from datetime import datetime
from decimal import Decimal
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import ConferenceRoom, ConferenceBooking
from .permissions import IsGuest, IsAdminOrStaff


def get_request_data(request):
    if hasattr(request, 'data') and request.data:
        return request.data
    return request.POST


def conference_to_dict(room):
    return {
        'id': room.id,
        'name': room.name,
        'capacity': room.capacity,
        'price_per_hour': str(room.price_per_hour),
        'features': room.features,
        'additional_packages': room.additional_packages,
        'is_active': room.is_active,
        'image': room.image.url if room.image else None,
        'created_at': room.created_at,
        'updated_at': room.updated_at,
    }


### ==================== LIST ALL CONFERENCE ROOMS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conference_list(request):
    rooms = ConferenceRoom.objects.filter(is_active=True)
    data = [conference_to_dict(r) for r in rooms]
    return Response(data)


### ==================== CHECK AVAILABILITY ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conference_available(request):
    booking_date = request.GET.get('date')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    guests = request.GET.get('guests', 0)

    if not all([booking_date, start_time, end_time]):
        return Response({'error': 'date, start_time, end_time required'}, status=status.HTTP_400_BAD_REQUEST)

    # CHANGED: Hide both pending and confirmed bookings
    booked_ids = ConferenceBooking.objects.filter(
        status__in=['confirmed', 'pending'], booking_date=booking_date,
        start_time__lt=end_time, end_time__gt=start_time
    ).values_list('conference_room_id', flat=True)

    rooms = ConferenceRoom.objects.filter(is_active=True).exclude(id__in=booked_ids)
    if guests and int(guests) > 0:
        rooms = rooms.filter(capacity__gte=int(guests))

    data = [conference_to_dict(r) for r in rooms]
    return Response({'date': booking_date, 'start_time': start_time, 'end_time': end_time, 'available_rooms': data})


### ==================== STAFF/ADMIN: ADD CONFERENCE ROOM ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def conference_create(request):
    data = get_request_data(request)
    name = data.get('name')
    capacity = data.get('capacity')
    price_per_hour = data.get('price_per_hour')

    if not all([name, capacity, price_per_hour]):
        return Response({'error': 'name, capacity, price_per_hour required'}, status=status.HTTP_400_BAD_REQUEST)

    if ConferenceRoom.objects.filter(name=name).exists():
        return Response({'error': 'Conference room name already exists'}, status=status.HTTP_400_BAD_REQUEST)

    room = ConferenceRoom.objects.create(
        name=name, capacity=capacity, price_per_hour=price_per_hour,
        features=data.get('features', ''),
        additional_packages=data.get('additional_packages', ''),
        image=request.FILES.get('image') if hasattr(request, 'FILES') else None,
    )
    return Response({'message': 'Conference room created', 'room_id': room.id, 'name': room.name}, status=status.HTTP_201_CREATED)


### ==================== STAFF/ADMIN: EDIT CONFERENCE ROOM ====================
@api_view(['PUT', 'POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def conference_update(request, room_id):
    try:
        room = ConferenceRoom.objects.get(id=room_id)
    except ConferenceRoom.DoesNotExist:
        return Response({'error': 'Conference room not found'}, status=status.HTTP_404_NOT_FOUND)

    data = get_request_data(request)
    room.name = data.get('name', room.name)
    room.capacity = data.get('capacity', room.capacity)
    room.price_per_hour = data.get('price_per_hour', room.price_per_hour)
    room.features = data.get('features', room.features)
    room.additional_packages = data.get('additional_packages', room.additional_packages)
    room.is_active = data.get('is_active', room.is_active)
    if hasattr(request, 'FILES') and 'image' in request.FILES:
        room.image = request.FILES['image']
    room.save()
    return Response({'message': 'Conference room updated'})


### ==================== STAFF/ADMIN: DELETE CONFERENCE ROOM ====================
@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def conference_delete(request, room_id):
    try:
        room = ConferenceRoom.objects.get(id=room_id)
        room.is_active = False
        room.save()
        return Response({'message': 'Conference room deactivated'})
    except ConferenceRoom.DoesNotExist:
        return Response({'error': 'Conference room not found'}, status=status.HTTP_404_NOT_FOUND)


### ==================== GUEST: BOOK CONFERENCE ROOM ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsGuest])
def conference_book(request):
    data = get_request_data(request)
    room_id = data.get('room_id')
    booking_date = data.get('date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    guests = data.get('guests', 1)
    selected_packages = data.get('selected_packages', [])

    if not all([room_id, booking_date, start_time, end_time]):
        return Response({'error': 'room_id, date, start_time, end_time required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        room = ConferenceRoom.objects.get(id=room_id, is_active=True)
    except ConferenceRoom.DoesNotExist:
        return Response({'error': 'Conference room not found'}, status=status.HTTP_404_NOT_FOUND)

    # CHANGED: Check for both pending and confirmed conflicts
    conflicting = ConferenceBooking.objects.filter(
        conference_room=room, status__in=['confirmed', 'pending'],
        booking_date=booking_date, start_time__lt=end_time, end_time__gt=start_time
    )
    if conflicting.exists():
        return Response({'error': 'Room not available for this time slot'}, status=status.HTTP_400_BAD_REQUEST)

    st = datetime.strptime(start_time, '%H:%M')
    et = datetime.strptime(end_time, '%H:%M')
    hours = (et - st).seconds / 3600
    if hours <= 0:
        return Response({'error': 'end_time must be after start_time'}, status=status.HTTP_400_BAD_REQUEST)

    base_price = Decimal(str(hours)) * room.price_per_hour

    package_prices = {}
    if room.additional_packages:
        for pkg in room.additional_packages.split(','):
            pkg = pkg.strip()
            if ':' in pkg:
                name, price = pkg.split(':')
                package_prices[name.strip()] = Decimal(price.strip())

    extra_charges = Decimal('0')
    for selected in selected_packages:
        if selected in package_prices:
            extra_charges += package_prices[selected]

    total_price = base_price + extra_charges

    booking = ConferenceBooking.objects.create(
        guest=request.user, conference_room=room,
        booking_date=booking_date, start_time=start_time, end_time=end_time,
        guests=guests, total_price=total_price,
        selected_packages=str(selected_packages),
        status='pending', payment_status='unpaid'
    )

    return Response({
        'message': 'Conference room booked. Pay via M-Pesa to confirm.',
        'booking': {
            'id': booking.id, 'room': room.name,
            'date': booking_date, 'time': f'{start_time} - {end_time}',
            'hours': hours, 'base_price': str(base_price),
            'selected_packages': selected_packages,
            'extra_charges': str(extra_charges),
            'total_price': str(total_price),
            'status': booking.status,
            'next_step': f'POST /api/mpesa/pay/ with booking_id: CONF-{booking.id}'
        }
    }, status=status.HTTP_201_CREATED)


### ==================== GUEST: MY CONFERENCE BOOKINGS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsGuest])
def my_conference_bookings(request):
    bookings = ConferenceBooking.objects.filter(guest=request.user).order_by('-created_at')
    data = []
    for b in bookings:
        data.append({
            'id': b.id, 'room': b.conference_room.name,
            'date': b.booking_date, 'time': f'{b.start_time} - {b.end_time}',
            'guests': b.guests, 'packages': b.selected_packages,
            'total_price': str(b.total_price),
            'status': b.status, 'payment_status': b.payment_status,
        })
    return Response({'bookings': data})


### ==================== GUEST: CANCEL CONFERENCE BOOKING ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsGuest])
def cancel_conference_booking(request, booking_id):
    try:
        booking = ConferenceBooking.objects.get(id=booking_id, guest=request.user)
    except ConferenceBooking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    if booking.status == 'completed':
        return Response({'error': 'Cannot cancel completed booking'}, status=status.HTTP_400_BAD_REQUEST)
    booking.status = 'cancelled'
    booking.save()
    return Response({'message': 'Booking cancelled'})


### ==================== GUEST: DELETE MY CONFERENCE BOOKING ====================
@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated, IsGuest])
def delete_my_conference_booking(request, booking_id):
    try:
        booking = ConferenceBooking.objects.get(id=booking_id, guest=request.user)
    except ConferenceBooking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    if booking.status not in ['completed', 'cancelled']:
        return Response({'error': 'Can only delete completed or cancelled bookings'}, status=status.HTTP_400_BAD_REQUEST)
    booking.delete()
    return Response({'message': 'Booking deleted'})


### ==================== STAFF/ADMIN: ALL CONFERENCE BOOKINGS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def all_conference_bookings(request):
    bookings = ConferenceBooking.objects.all().order_by('-created_at')
    data = []
    for b in bookings:
        data.append({
            'id': b.id, 'guest': b.guest.username, 'room': b.conference_room.name,
            'date': b.booking_date, 'time': f'{b.start_time} - {b.end_time}',
            'guests': b.guests, 'packages': b.selected_packages,
            'total_price': str(b.total_price),
            'status': b.status, 'payment_status': b.payment_status,
        })
    return Response({'bookings': data})


### ==================== STAFF/ADMIN: COMPLETE CONFERENCE BOOKING ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def complete_conference_booking(request, booking_id):
    try:
        booking = ConferenceBooking.objects.get(id=booking_id)
    except ConferenceBooking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    if booking.status != 'confirmed':
        return Response({'error': 'Booking must be confirmed first'}, status=status.HTTP_400_BAD_REQUEST)
    booking.status = 'completed'
    booking.save()
    return Response({'message': f'Conference room {booking.conference_room.name} is now available.'})


### ==================== STAFF/ADMIN: DELETE CONFERENCE BOOKING ====================
@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def delete_conference_booking(request, booking_id):
    try:
        booking = ConferenceBooking.objects.get(id=booking_id)
    except ConferenceBooking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    if booking.status in ['pending', 'confirmed']:
        return Response({'error': 'Cannot delete active booking'}, status=status.HTTP_400_BAD_REQUEST)
    booking.delete()
    return Response({'message': 'Conference booking deleted'})