import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Room


@api_view(['GET'])
def room_list(request):
    """List all active rooms"""
    rooms = Room.objects.filter(is_active=True).values()
    return Response(rooms)


@api_view(['GET'])
def room_detail(request, room_id):
    """Get single room"""
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


@api_view(['POST'])
def room_create(request):
    """Add new room"""
    room_number = request.POST.get('room_number')
    room_type = request.POST.get('room_type')
    price_per_night = request.POST.get('price_per_night')
    max_guests = request.POST.get('max_guests')

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
        description=request.POST.get('description', ''),
        amenities=request.POST.get('amenities', ''),
        image=request.FILES.get('image'),
    )

    return Response({
        'message': 'Room created',
        'room_id': room.id,
        'image_url': request.build_absolute_uri(room.image.url) if room.image else None,
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'POST'])
def room_update(request, room_id):
    """Edit room"""
    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)

    room.room_number = request.POST.get('room_number', room.room_number)
    room.room_type = request.POST.get('room_type', room.room_type)
    room.price_per_night = request.POST.get('price_per_night', room.price_per_night)
    room.max_guests = request.POST.get('max_guests', room.max_guests)
    room.description = request.POST.get('description', room.description)
    room.amenities = request.POST.get('amenities', room.amenities)
    room.is_active = request.POST.get('is_active', room.is_active)

    if 'image' in request.FILES:
        room.image = request.FILES['image']

    room.save()
    return Response({'message': 'Room updated', 'room_id': room.id})


@api_view(['DELETE', 'POST'])
def room_delete(request, room_id):
    """Deactivate room"""
    try:
        room = Room.objects.get(id=room_id)
        room.is_active = False
        room.save()
        return Response({'message': 'Room deactivated'})
    except Room.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def room_available(request):
    """Check available rooms by date"""
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')

    if not check_in or not check_out:
        return Response(
            {'error': 'check_in and check_out required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    rooms = Room.objects.filter(is_active=True).values()
    return Response(list(rooms))