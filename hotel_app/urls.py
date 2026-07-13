from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import render
from hotel_app import room_views, table_views, conference_views, venue_views, staff_views, refund_views
from hotel_app.auth_views import (
    RegisterView, LoginView, LogoutView, CurrentUserView,
    GuestDashboardView, StaffDashboardView, ChangePasswordView,
    CheckForcePasswordChangeView
)
from hotel_app.admin_views import (
    AdminDashboardView, UnapproveStaffView, UserListView, PendingStaffView,
    ApproveStaffView, RejectStaffView,
    ListGuestsView, ListStaffView, ListAdminsView, DeleteUserView,
    AdminCreateStaffView, CreateAdminView, UpdateUserRoleView,
    AdminChangeStaffPasswordView, AdminAnalyticsView  # Added AdminAnalyticsView
)
from hotel_app import profile_views


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

    ### ==================== MPESA API ====================
    path("api/mpesa/", include("hotel_app.mpesa_urls")),

    ### ==================== AUTH ====================
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/me/', CurrentUserView.as_view(), name='current_user'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('api/auth/check-password-change/', CheckForcePasswordChangeView.as_view(), name='check_password_change'),

    ### ==================== DASHBOARDS ====================
    path('api/guest/dashboard/', GuestDashboardView.as_view(), name='guest_dashboard'),
    path('api/staff/dashboard/', StaffDashboardView.as_view(), name='staff_dashboard'),
    path('api/admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),

    ### ==================== STAFF ANALYTICS ====================
    path('api/staff/analytics/', staff_views.staff_analytics, name='staff_analytics'),

    ### ==================== ADMIN ANALYTICS ====================
    path('api/admin/analytics/', AdminAnalyticsView.as_view(), name='admin_analytics'),

    ### ==================== ADMIN USER MANAGEMENT ====================
    path('api/admin/users/', UserListView.as_view(), name='admin_users'),
    path('api/admin/guests/', ListGuestsView.as_view(), name='admin_guests'),
    path('api/admin/staff/', ListStaffView.as_view(), name='admin_staff_list'),
    path('api/admin/admins/', ListAdminsView.as_view(), name='admin_admins'),
    path('api/admin/staff/pending/', PendingStaffView.as_view(), name='admin_pending_staff'),
    path('api/admin/staff/approve/', ApproveStaffView.as_view(), name='admin_approve_staff'),
    path('api/admin/staff/unapprove/', UnapproveStaffView.as_view(), name='admin_unapprove_staff'),
    path('api/admin/staff/reject/', RejectStaffView.as_view(), name='admin_reject_staff'),
    path('api/admin/users/<int:user_id>/delete/', DeleteUserView.as_view(), name='admin_delete_user'),
    path('api/admin/users/<int:user_id>/role/', UpdateUserRoleView.as_view(), name='update_user_role'),
    
    ### ==================== ADMIN CHANGE STAFF PASSWORD ====================
    path('api/admin/users/<int:user_id>/change-password/', 
         AdminChangeStaffPasswordView.as_view(), 
         name='admin_change_staff_password'),

    ### ==================== ADMIN CREATE STAFF ====================
    path('api/admin/staff/create/', AdminCreateStaffView.as_view(), name='admin_create_staff'),
    path('api/auth/create-admin/', CreateAdminView.as_view(), name='create_admin'),

    ### ==================== CANCELLATION & REFUND ====================
    path('api/cancellation/request/', refund_views.RequestCancellationView.as_view(), name='request_cancellation'),
    path('api/cancellation/requests/', refund_views.ViewCancellationRequestsView.as_view(), name='view_cancellation_requests'),
    path('api/cancellation/<int:request_id>/approve/', refund_views.ApproveCancellationView.as_view(), name='approve_cancellation'),
    path('api/cancellation/<int:request_id>/reject/', refund_views.RejectCancellationView.as_view(), name='reject_cancellation'),
    path('api/refund/<int:refund_id>/process/', refund_views.ProcessRefundView.as_view(), name='process_refund'),

    ### ==================== PROFILE ====================
    path('api/profile/', profile_views.GetProfileView.as_view(), name='get_profile'),
    path('api/profile/update-password/', profile_views.UpdatePasswordView.as_view(), name='update_password'),
    path('api/profile/delete-account/', profile_views.DeleteAccountView.as_view(), name='delete_account'),

    ### ==================== ROOMS ====================
    path('api/rooms/', room_views.room_list, name='room_list'),
    path('api/rooms/available/', room_views.room_available, name='room_available'),
    path('api/rooms/<int:room_id>/', room_views.room_detail, name='room_detail'),
    path('api/rooms/create/', room_views.room_create, name='room_create'),
    path('api/rooms/<int:room_id>/update/', room_views.room_update, name='room_update'),
    path('api/rooms/<int:room_id>/delete/', room_views.room_delete, name='room_delete'),
    path('api/rooms/book/', room_views.book_room, name='book_room'),
    path('api/rooms/my-bookings/', room_views.my_bookings, name='my_bookings'),
    path('api/rooms/<int:booking_id>/cancel/', room_views.cancel_booking, name='cancel_booking'),
    path('api/rooms/all-bookings/', room_views.all_bookings, name='all_bookings'),
    path('api/rooms/<int:booking_id>/check-in/', room_views.check_in, name='check_in'),
    path('api/rooms/<int:booking_id>/check-out/', room_views.check_out, name='check_out'),
    path('api/rooms/booking/<int:booking_id>/delete/', room_views.delete_booking, name='delete_booking'),
    path('api/rooms/my-booking/<int:booking_id>/delete/', room_views.delete_my_booking, name='delete_my_booking'),

    ### ==================== RESTAURANT TABLES ====================
    path('api/tables/', table_views.table_list, name='table_list'),
    path('api/tables/available/', table_views.table_available, name='table_available'),
    path('api/tables/create/', table_views.table_create, name='table_create'),
    path('api/tables/<int:table_id>/update/', table_views.table_update, name='table_update'),
    path('api/tables/<int:table_id>/delete/', table_views.table_delete, name='table_delete'),
    path('api/tables/reserve/', table_views.reserve_table, name='reserve_table'),
    path('api/tables/my-bookings/', table_views.my_table_bookings, name='my_table_bookings'),
    path('api/tables/<int:booking_id>/cancel/', table_views.cancel_table_booking, name='cancel_table_booking'),
    path('api/tables/all-bookings/', table_views.all_table_bookings, name='all_table_bookings'),
    path('api/tables/<int:booking_id>/complete/', table_views.complete_table_booking, name='complete_table_booking'),
    path('api/tables/booking/<int:booking_id>/delete/', table_views.delete_table_booking, name='delete_table_booking'),
    path('api/tables/my-booking/<int:booking_id>/delete/', table_views.delete_my_table_booking, name='delete_my_table_booking'),

    ### ==================== CONFERENCE ROOMS ====================
    path('api/conference/', conference_views.conference_list, name='conference_list'),
    path('api/conference/available/', conference_views.conference_available, name='conference_available'),
    path('api/conference/create/', conference_views.conference_create, name='conference_create'),
    path('api/conference/<int:room_id>/update/', conference_views.conference_update, name='conference_update'),
    path('api/conference/<int:room_id>/delete/', conference_views.conference_delete, name='conference_delete'),
    path('api/conference/book/', conference_views.conference_book, name='conference_book'),
    path('api/conference/my-bookings/', conference_views.my_conference_bookings, name='my_conference_bookings'),
    path('api/conference/<int:booking_id>/cancel/', conference_views.cancel_conference_booking, name='cancel_conference_booking'),
    path('api/conference/my-booking/<int:booking_id>/delete/', conference_views.delete_my_conference_booking, name='delete_my_conference_booking'),
    path('api/conference/all-bookings/', conference_views.all_conference_bookings, name='all_conference_bookings'),
    path('api/conference/<int:booking_id>/complete/', conference_views.complete_conference_booking, name='complete_conference_booking'),
    path('api/conference/booking/<int:booking_id>/delete/', conference_views.delete_conference_booking, name='delete_conference_booking'),

    ### ==================== VENUES ====================
    path('api/venues/', venue_views.venue_list, name='venue_list'),
    path('api/venues/available/', venue_views.venue_available, name='venue_available'),
    path('api/venues/create/', venue_views.venue_create, name='venue_create'),
    path('api/venues/<int:venue_id>/update/', venue_views.venue_update, name='venue_update'),
    path('api/venues/<int:venue_id>/delete/', venue_views.venue_delete, name='venue_delete'),
    path('api/venues/book/', venue_views.venue_book, name='venue_book'),
    path('api/venues/my-bookings/', venue_views.my_venue_bookings, name='my_venue_bookings'),
    path('api/venues/<int:booking_id>/cancel/', venue_views.cancel_venue_booking, name='cancel_venue_booking'),
    path('api/venues/my-booking/<int:booking_id>/delete/', venue_views.delete_my_venue_booking, name='delete_my_venue_booking'),
    path('api/venues/all-bookings/', venue_views.all_venue_bookings, name='all_venue_bookings'),
    path('api/venues/<int:booking_id>/complete/', venue_views.complete_venue_booking, name='complete_venue_booking'),
    path('api/venues/booking/<int:booking_id>/delete/', venue_views.delete_venue_booking, name='delete_venue_booking'),
]