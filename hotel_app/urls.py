from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import render
from hotel_app import room_views
from hotel_app.auth_views import (
    RegisterView, LoginView, LogoutView, CurrentUserView,
    GuestDashboardView, StaffDashboardView
)
from hotel_app.admin_views import (
    AdminDashboardView, UserListView, PendingStaffView,
    ApproveStaffView, RejectStaffView
)


### ==================== PUBLIC DASHBOARD ====================
def public_dashboard(request):
    return JsonResponse({
        'hotel': 'Grand Horizon Hotel',
        'welcome': 'Discover luxury and comfort in the heart of the city.',
        'services': ['Rooms', 'Restaurant', 'Conference Rooms', 'Event Venues'],
        'links': {
            'register': '/api/auth/register/',
            'login': '/api/auth/login/',
        }
    })


### ==================== MPESA TEST PAGE ====================
def mpesa_test_page(request):
    return render(request, "mpesa_test.html")


urlpatterns = [
    ### ==================== HOME ====================
    path('', public_dashboard, name='home'),

    ### ==================== MPESA TEST PAGE ====================
    path("mpesa-test/", mpesa_test_page, name="mpesa_test"),

    ### ==================== MPESA API (DO NOT TOUCH) ====================
    path("api/mpesa/", include("hotel_app.mpesa_urls")),

    ### ==================== AUTH ====================
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/me/', CurrentUserView.as_view(), name='current_user'),

    ### ==================== DASHBOARDS ====================
    path('api/guest/dashboard/', GuestDashboardView.as_view(), name='guest_dashboard'),
    path('api/staff/dashboard/', StaffDashboardView.as_view(), name='staff_dashboard'),
    path('api/admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),

    ### ==================== ADMIN USER MANAGEMENT ====================
    path('api/admin/users/', UserListView.as_view(), name='admin_users'),
    path('api/admin/staff/pending/', PendingStaffView.as_view(), name='admin_pending_staff'),
    path('api/admin/staff/approve/', ApproveStaffView.as_view(), name='admin_approve_staff'),
    path('api/admin/staff/reject/', RejectStaffView.as_view(), name='admin_reject_staff'),

    ### ==================== ROOMS (MANAGEMENT + BOOKING) ====================
    # Staff/Admin manage rooms
    path('api/rooms/', room_views.room_list, name='room_list'),
    path('api/rooms/available/', room_views.room_available, name='room_available'),
    path('api/rooms/<int:room_id>/', room_views.room_detail, name='room_detail'),
    path('api/rooms/create/', room_views.room_create, name='room_create'),
    path('api/rooms/<int:room_id>/update/', room_views.room_update, name='room_update'),
    path('api/rooms/<int:room_id>/delete/', room_views.room_delete, name='room_delete'),

    # Guest books room
    path('api/rooms/book/', room_views.book_room, name='book_room'),

    # Guest views their bookings
    path('api/rooms/my-bookings/', room_views.my_bookings, name='my_bookings'),

    # Guest cancels booking
    path('api/rooms/<int:booking_id>/cancel/', room_views.cancel_booking, name='cancel_booking'),

    # Staff views all bookings
    path('api/rooms/all-bookings/', room_views.all_bookings, name='all_bookings'),

    # Staff check-in / check-out
    path('api/rooms/<int:booking_id>/check-in/', room_views.check_in, name='check_in'),
    path('api/rooms/<int:booking_id>/check-out/', room_views.check_out, name='check_out'),
]