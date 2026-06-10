from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Room


### ==================== PUBLIC HOTEL DASHBOARD ====================
# Anyone can see this — no JWT required.
# Shows a general overview of the hotel: total rooms, room types, prices.
@api_view(['GET'])
@permission_classes([AllowAny])
def public_hotel_dashboard(request):
    rooms = Room.objects.filter(is_active=True)
    
    room_data = []
    for room in rooms:
        room_data.append({
            'room_number': room.room_number,
            'room_type': room.room_type,
            'price_per_night': str(room.price_per_night),
            'max_guests': room.max_guests,
            'description': room.description,
            'amenities': room.amenities,
        })

    return Response({
        'hotel': 'Welcome to Our Hotel',
        'total_rooms': rooms.count(),
        'room_types': {
            'single': rooms.filter(room_type='single').count(),
            'double': rooms.filter(room_type='double').count(),
            'suite': rooms.filter(room_type='suite').count(),
            'family': rooms.filter(room_type='family').count(),
        },
        'rooms': room_data,
        'links': {
            'register': '/api/auth/register/',
            'login': '/api/auth/login/',
            'guest_dashboard': '/api/guest/dashboard/',
            'staff_dashboard': '/api/staff/dashboard/',
            'admin_dashboard': '/api/admin/dashboard/',
        }
    })