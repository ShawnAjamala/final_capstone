from datetime import datetime, date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import RestaurantTable, TableBooking
from .permissions import IsGuest, IsAdminOrStaff


### ==================== HELPER ====================
def get_request_data(request):
    if hasattr(request, 'data') and request.data:
        return request.data
    return request.POST


### ==================== LIST ALL ACTIVE TABLES ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def table_list(request):
    tables = RestaurantTable.objects.filter(is_active=True).values()
    return Response(tables)


### ==================== CHECK AVAILABLE TABLES BY DATE & TIME ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def table_available(request):
    reservation_date = request.GET.get('date')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    guests = request.GET.get('guests', 1)

    if not all([reservation_date, start_time, end_time]):
        return Response(
            {'error': 'date, start_time, end_time required (HH:MM)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Find tables already booked during this time slot
    booked_table_ids = TableBooking.objects.filter(
        status='confirmed',
        reservation_date=reservation_date,
        start_time__lt=end_time,
        end_time__gt=start_time
    ).values_list('table_id', flat=True)

    available = RestaurantTable.objects.filter(
        is_active=True,
        capacity__gte=guests
    ).exclude(id__in=booked_table_ids).values()

    return Response({
        'date': reservation_date,
        'start_time': start_time,
        'end_time': end_time,
        'guests': guests,
        'available_tables': list(available)
    })


### ==================== STAFF/ADMIN: ADD TABLE ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def table_create(request):
    data = get_request_data(request)

    table_number = data.get('table_number')
    capacity = data.get('capacity')
    price_per_slot = data.get('price_per_slot')

    if not all([table_number, capacity, price_per_slot]):
        return Response(
            {'error': 'table_number, capacity, price_per_slot required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if RestaurantTable.objects.filter(table_number=table_number).exists():
        return Response({'error': 'Table number already exists'}, status=status.HTTP_400_BAD_REQUEST)

    table = RestaurantTable.objects.create(
        table_number=table_number,
        capacity=capacity,
        price_per_slot=price_per_slot,
        location=data.get('location', ''),
        image=request.FILES.get('image') if hasattr(request, 'FILES') else None,
    )

    return Response({
        'message': 'Table created',
        'table_id': table.id,
        'table_number': table.table_number,
    }, status=status.HTTP_201_CREATED)


### ==================== STAFF/ADMIN: EDIT TABLE ====================
@api_view(['PUT', 'POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def table_update(request, table_id):
    try:
        table = RestaurantTable.objects.get(id=table_id)
    except RestaurantTable.DoesNotExist:
        return Response({'error': 'Table not found'}, status=status.HTTP_404_NOT_FOUND)

    data = get_request_data(request)
    table.table_number = data.get('table_number', table.table_number)
    table.capacity = data.get('capacity', table.capacity)
    table.price_per_slot = data.get('price_per_slot', table.price_per_slot)
    table.location = data.get('location', table.location)
    table.is_active = data.get('is_active', table.is_active)

    if hasattr(request, 'FILES') and 'image' in request.FILES:
        table.image = request.FILES['image']

    table.save()
    return Response({'message': 'Table updated'})


### ==================== STAFF/ADMIN: DELETE TABLE ====================
@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def table_delete(request, table_id):
    try:
        table = RestaurantTable.objects.get(id=table_id)
        table.is_active = False
        table.save()
        return Response({'message': 'Table deactivated'})
    except RestaurantTable.DoesNotExist:
        return Response({'error': 'Table not found'}, status=status.HTTP_404_NOT_FOUND)


### ==================== GUEST: RESERVE TABLE ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsGuest])
def reserve_table(request):
    data = get_request_data(request)

    table_id = data.get('table_id')
    reservation_date = data.get('date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    guests = data.get('guests', 1)

    if not all([table_id, reservation_date, start_time, end_time]):
        return Response(
            {'error': 'table_id, date, start_time, end_time required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        table = RestaurantTable.objects.get(id=table_id, is_active=True)
    except RestaurantTable.DoesNotExist:
        return Response({'error': 'Table not found'}, status=status.HTTP_404_NOT_FOUND)

    if guests > table.capacity:
        return Response({'error': f'Table capacity is {table.capacity}'}, status=status.HTTP_400_BAD_REQUEST)

    # Check for overlapping confirmed bookings
    conflicting = TableBooking.objects.filter(
        table=table,
        status='confirmed',
        reservation_date=reservation_date,
        start_time__lt=end_time,
        end_time__gt=start_time
    )
    if conflicting.exists():
        return Response({'error': 'Table not available for this time slot'}, status=status.HTTP_400_BAD_REQUEST)

    booking = TableBooking.objects.create(
        guest=request.user,
        table=table,
        reservation_date=reservation_date,
        start_time=start_time,
        end_time=end_time,
        guests=guests,
        total_price=table.price_per_slot,
        status='pending',
        payment_status='unpaid'
    )

    return Response({
        'message': 'Table reserved. Pay via M-Pesa to confirm.',
        'booking': {
            'id': booking.id,
            'table': table.table_number,
            'date': reservation_date,
            'time': f'{start_time} - {end_time}',
            'guests': guests,
            'total_price': str(booking.total_price),
            'status': booking.status,
            'next_step': f'POST /api/mpesa/pay/ with booking_id: TBL-{booking.id}'
        }
    }, status=status.HTTP_201_CREATED)


### ==================== GUEST: MY TABLE BOOKINGS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsGuest])
def my_table_bookings(request):
    bookings = TableBooking.objects.filter(guest=request.user).order_by('-created_at')
    data = []
    for b in bookings:
        data.append({
            'id': b.id,
            'table': b.table.table_number,
            'date': b.reservation_date,
            'time': f'{b.start_time} - {b.end_time}',
            'guests': b.guests,
            'total_price': str(b.total_price),
            'status': b.status,
            'payment_status': b.payment_status,
        })
    return Response({'bookings': data})


### ==================== GUEST: CANCEL TABLE BOOKING ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsGuest])
def cancel_table_booking(request, booking_id):
    try:
        booking = TableBooking.objects.get(id=booking_id, guest=request.user)
    except TableBooking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

    if booking.status == 'completed':
        return Response({'error': 'Cannot cancel completed booking'}, status=status.HTTP_400_BAD_REQUEST)

    booking.status = 'cancelled'
    booking.save()
    return Response({'message': 'Booking cancelled. Table is now available.'})


### ==================== STAFF/ADMIN: ALL TABLE BOOKINGS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def all_table_bookings(request):
    bookings = TableBooking.objects.all().order_by('-created_at')
    data = []
    for b in bookings:
        data.append({
            'id': b.id,
            'guest': b.guest.username,
            'table': b.table.table_number,
            'date': b.reservation_date,
            'time': f'{b.start_time} - {b.end_time}',
            'guests': b.guests,
            'total_price': str(b.total_price),
            'status': b.status,
            'payment_status': b.payment_status,
        })
    return Response({'bookings': data})


### ==================== STAFF/ADMIN: COMPLETE TABLE BOOKING ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def complete_table_booking(request, booking_id):
    try:
        booking = TableBooking.objects.get(id=booking_id)
    except TableBooking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

    if booking.status != 'confirmed':
        return Response({'error': 'Booking must be confirmed first'}, status=status.HTTP_400_BAD_REQUEST)

    booking.status = 'completed'
    booking.save()
    return Response({'message': f'Table {booking.table.table_number} is now available.'})

### ==================== STAFF/ADMIN: DELETE TABLE BOOKING ====================
@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])
def delete_table_booking(request, booking_id):
    try:
        booking = TableBooking.objects.get(id=booking_id)
    except TableBooking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

    if booking.status in ['pending', 'confirmed']:
        return Response(
            {'error': 'Cannot delete active booking. Cancel or complete first.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    booking.delete()
    return Response({'message': 'Table booking deleted permanently'})


### ==================== GUEST: DELETE MY COMPLETED TABLE BOOKING ====================
@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated, IsGuest])
def delete_my_table_booking(request, booking_id):
    try:
        booking = TableBooking.objects.get(id=booking_id, guest=request.user)
    except TableBooking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

    if booking.status not in ['completed', 'cancelled']:
        return Response(
            {'error': 'Can only delete completed or cancelled bookings'},
            status=status.HTTP_400_BAD_REQUEST
        )

    booking.delete()
    return Response({'message': 'Table booking deleted'})