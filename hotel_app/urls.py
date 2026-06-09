from django.urls import path, include
from django.shortcuts import render
from hotel_app import room_views  # Changed from views

def mpesa_test_page(request):
    return render(request, "mpesa_test.html")

urlpatterns = [
    path("", mpesa_test_page, name="mpesa_test"),
    path("api/mpesa/", include("hotel_app.mpesa_urls")),

    # Rooms
    path('api/rooms/', room_views.room_list, name='room_list'),
    path('api/rooms/available/', room_views.room_available, name='room_available'),
    path('api/rooms/<int:room_id>/', room_views.room_detail, name='room_detail'),
    path('api/rooms/create/', room_views.room_create, name='room_create'),
    path('api/rooms/<int:room_id>/update/', room_views.room_update, name='room_update'),
    path('api/rooms/<int:room_id>/delete/', room_views.room_delete, name='room_delete'),
]