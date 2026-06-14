import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Room, Booking
from .permissions import IsGuest, IsStaff, IsAdmin, IsAdminOrStaff




### ==================== HELPER ====================
def get_request_data(request):
    if hasattr(request, 'data') and request.data:
        return request.data
    return request.POST


### ==================== LIST ALL ACTIVE ROOMS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def room_list(request):
    rooms = Room.objects.filter(is_active=True).values()
    return Response(rooms)


### ==================== CHECK AVAILABLE ROOMS BY DATE ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def room_available(request):
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')

    if not check_in or not check_out:
        return Response(
            {'error': 'check_in and check_out required (YYYY-MM-DD)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    booked_room_ids = Booking.objects.filter(
        status__in=['confirmed', 'checked_in'],
        check_in__lt=check_out,
        check_out__gt=check_in
    ).values_list('room_id', flat=True)

    available = Room.objects.filter(is_active=True).exclude(id__in=booked_room_ids).values()

    return Response({
        'check_in': check_in,
        'check_out': check_out,
        'available_rooms': list(available)
    })


### ==================== GET SINGLE ROOM ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def room_detail(request, room_id):
    try:
        room = Room.objects.get(id=room_id)
        data = {
            'id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type,
            'price_per_night': str(room.price_per_night),
            'max_guests': room.max_guests,
            'description': room.description,
            'amenities': room.amenities,
            'is_active': room.is_active,
            'image': request.build_absolute_uri(room.image.url) if room.image else None,
        }
        return Response(data)
    except Room.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


### ==================== STAFF/ADMIN: ADD ROOM ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def room_create(request):
    data = get_request_data(request)

    room_number = data.get('room_number')
    room_type = data.get('room_type')
    price_per_night = data.get('price_per_night')
    max_guests = data.get('max_guests')

    if not all([room_number, room_type, price_per_night, max_guests]):
        return Response(
            {'error': 'room_number, room_type, price_per_night, max_guests required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if Room.objects.filter(room_number=room_number).exists():
        return Response({'error': 'Room number already exists'}, status=status.HTTP_400_BAD_REQUEST)

    room = Room.objects.create(
        room_number=room_number,
        room_type=room_type,
        price_per_night=price_per_night,
        max_guests=max_guests,
        description=data.get('description', ''),
        amenities=data.get('amenities', ''),
        image=request.FILES.get('image') if hasattr(request, 'FILES') else None,
    )

    return Response({
        'message': 'Room created successfully',
        'room_id': room.id,
        'room_number': room.room_number,
    }, status=status.HTTP_201_CREATED)


### ==================== STAFF/ADMIN: EDIT ROOM ====================
@api_view(['PUT', 'POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def room_update(request, room_id):
    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)

    data = get_request_data(request)

    room.room_number = data.get('room_number', room.room_number)
    room.room_type = data.get('room_type', room.room_type)
    room.price_per_night = data.get('price_per_night', room.price_per_night)
    room.max_guests = data.get('max_guests', room.max_guests)
    room.description = data.get('description', room.description)
    room.amenities = data.get('amenities', room.amenities)
    room.is_active = data.get('is_active', room.is_active)

    if hasattr(request, 'FILES') and 'image' in request.FILES:
        room.image = request.FILES['image']

    room.save()
    return Response({'message': 'Room updated', 'room_id': room.id})


### ==================== STAFF/ADMIN: DELETE ROOM ====================
@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def room_delete(request, room_id):
    try:
        room = Room.objects.get(id=room_id)
        room.is_active = False
        room.save()
        return Response({'message': 'Room deactivated'})
    except Room.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


### ==================== GUEST: BOOK A ROOM ====================
# Creates booking (pending/unpaid). Guest must pay via M-Pesa to confirm.
# M-Pesa callback auto-updates status to confirmed/paid.
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsGuest])
def book_room(request):
    data = get_request_data(request)

    room_id = data.get('room_id')
    check_in = data.get('check_in')
    check_out = data.get('check_out')
    guests = data.get('guests', 1)

    if not all([room_id, check_in, check_out]):
        return Response(
            {'error': 'room_id, check_in, check_out required (YYYY-MM-DD)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        room = Room.objects.get(id=room_id, is_active=True)
    except Room.DoesNotExist:
        return Response({'error': 'Room not found or inactive'}, status=status.HTTP_404_NOT_FOUND)

    conflicting = Booking.objects.filter(
        room=room,
        status__in=['confirmed', 'checked_in'],
        check_in__lt=check_out,
        check_out__gt=check_in
    )
    if conflicting.exists():
        return Response(
            {'error': 'Room is not available for these dates'},
            status=status.HTTP_400_BAD_REQUEST
        )

    ci = datetime.strptime(check_in, '%Y-%m-%d')
    co = datetime.strptime(check_out, '%Y-%m-%d')
    nights = (co - ci).days
    if nights <= 0:
        return Response({'error': 'check_out must be after check_in'}, status=status.HTTP_400_BAD_REQUEST)

    total_price = nights * room.price_per_night

    booking = Booking.objects.create(
        guest=request.user,
        room=room,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        total_price=total_price,
        status='pending',
        payment_status='unpaid'
    )

    return Response({
        'message': 'Room booked. Pay via M-Pesa to confirm.',
        'booking': {
            'id': booking.id,
            'room': room.room_number,
            'room_type': room.room_type,
            'check_in': check_in,
            'check_out': check_out,
            'nights': nights,
            'total_price': str(total_price),
            'status': booking.status,
            'payment_status': booking.payment_status,
            'next_step': f'POST /api/mpesa/pay/ with booking_id: {booking.id}'
        }
    }, status=status.HTTP_201_CREATED)


### ==================== GUEST: MY BOOKINGS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsGuest])
def my_bookings(request):
    bookings = Booking.objects.filter(guest=request.user).order_by('-created_at')
    data = []
    for b in bookings:
        data.append({
            'id': b.id,
            'room': b.room.room_number,
            'room_type': b.room.room_type,
            'check_in': b.check_in,
            'check_out': b.check_out,
            'total_price': str(b.total_price),
            'status': b.status,
            'payment_status': b.payment_status,
        })
    return Response({'bookings': data})


### ==================== GUEST: CANCEL BOOKING ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsGuest])
def cancel_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, guest=request.user)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

    if booking.status in ['checked_in', 'checked_out']:
        return Response(
            {'error': 'Cannot cancel. Guest already checked in or out.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    booking.status = 'cancelled'
    booking.save()
    return Response({'message': 'Booking cancelled. Room is now available.'})


### ==================== STAFF/ADMIN: ALL BOOKINGS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def all_bookings(request):
    bookings = Booking.objects.all().order_by('-created_at')
    data = []
    for b in bookings:
        data.append({
            'id': b.id,
            'guest': b.guest.username,
            'room': b.room.room_number,
            'check_in': b.check_in,
            'check_out': b.check_out,
            'guests': b.guests,
            'total_price': str(b.total_price),
            'status': b.status,
            'payment_status': b.payment_status,
        })
    return Response({'bookings': data})


### ==================== STAFF/ADMIN: CHECK IN ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def check_in(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

    if booking.status != 'confirmed':
        return Response(
            {'error': 'Booking must be confirmed (paid) before check-in'},
            status=status.HTTP_400_BAD_REQUEST
        )

    booking.status = 'checked_in'
    booking.save()
    return Response({
        'message': f'Guest checked into Room {booking.room.room_number}.',
        'booking_id': booking.id
    })


### ==================== STAFF/ADMIN: CHECK OUT ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def check_out(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

    if booking.status != 'checked_in':
        return Response(
            {'error': 'Guest must be checked in first'},
            status=status.HTTP_400_BAD_REQUEST
        )

    booking.status = 'checked_out'
    booking.save()
    return Response({
        'message': f'Guest checked out. Room {booking.room.room_number} is now available.',
        'booking_id': booking.id
    })
### ==================== STAFF/ADMIN: DELETE BOOKING ====================
# Only for completed or cancelled bookings. Active bookings cannot be deleted.
@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def delete_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

    if booking.status in ['pending', 'confirmed', 'checked_in']:
        return Response(
            {'error': 'Cannot delete active booking. Cancel or check-out first.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    booking.delete()
    return Response({'message': 'Booking deleted permanently'})


### ==================== GUEST: DELETE MY COMPLETED BOOKING ====================
@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated, IsGuest])
def delete_my_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, guest=request.user)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

    if booking.status not in ['completed', 'cancelled']:
        return Response(
            {'error': 'Can only delete completed or cancelled bookings'},
            status=status.HTTP_400_BAD_REQUEST
        )

    booking.delete()
    return Response({'message': 'Booking deleted'})
