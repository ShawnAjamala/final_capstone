# hotel_app/refund_views.py

from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import (
    Booking, TableBooking, ConferenceBooking, VenueBooking,
    CancellationRequest, Refund, UserProfile
)
from .permissions import IsGuest, IsAdminOrStaff


### ==================== GUEST: REQUEST CANCELLATION ====================
class RequestCancellationView(APIView):
    permission_classes = [IsAuthenticated, IsGuest]

    def post(self, request):
        booking_id = request.data.get('booking_id')
        booking_type = request.data.get('booking_type')
        reason = request.data.get('reason')

        if not all([booking_id, booking_type, reason]):
            return Response(
                {'error': 'booking_id, booking_type, and reason are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking_models = {
            'room': Booking,
            'table': TableBooking,
            'conference': ConferenceBooking,
            'venue': VenueBooking,
        }

        if booking_type not in booking_models:
            return Response(
                {'error': 'Invalid booking type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        model_class = booking_models[booking_type]

        try:
            booking = model_class.objects.get(id=booking_id, guest=request.user)
        except model_class.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if booking.status in ['cancelled', 'completed', 'checked_out']:
            return Response(
                {'error': 'This booking cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if booking.status == 'cancellation_requested':
            return Response(
                {'error': 'Cancellation already requested for this booking'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if booking.payment_status != 'paid':
            return Response(
                {'error': 'Only paid bookings can be cancelled and refunded'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cancellation_request = CancellationRequest.objects.create(
            booking_id=booking_id,
            booking_type=booking_type,
            guest=request.user,
            reason=reason,
            status='pending'
        )

        booking.status = 'cancellation_requested'
        booking.cancellation_reason = reason
        booking.save()

        return Response({
            'message': 'Cancellation request submitted successfully',
            'request_id': cancellation_request.id,
            'booking_id': booking.id,
            'booking_type': booking_type,
            'status': 'pending'
        }, status=status.HTTP_201_CREATED)


### ==================== STAFF/ADMIN: VIEW CANCELLATION REQUESTS ====================
class ViewCancellationRequestsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrStaff]

    def get(self, request):
        status_filter = request.GET.get('status', 'pending')
        
        requests = CancellationRequest.objects.filter(status=status_filter).order_by('-created_at')
        
        data = []
        for req in requests:
            booking_models = {
                'room': Booking,
                'table': TableBooking,
                'conference': ConferenceBooking,
                'venue': VenueBooking,
            }
            
            booking_details = None
            if req.booking_type in booking_models:
                try:
                    booking = booking_models[req.booking_type].objects.get(id=req.booking_id)
                    booking_details = {
                        'total_price': str(booking.total_price),
                        'status': booking.status,
                        'payment_status': booking.payment_status,
                    }
                except:
                    pass
            
            data.append({
                'id': req.id,
                'booking_id': req.booking_id,
                'booking_type': req.booking_type,
                'guest': req.guest.username,
                'guest_email': req.guest.email,
                'reason': req.reason,
                'status': req.status,
                'created_at': req.created_at,
                'refund_amount': str(req.refund_amount) if req.refund_amount else None,
                'staff_notes': req.staff_notes,
                'booking_details': booking_details,
            })
        
        return Response({
            'requests': data,
            'total': len(data)
        })


### ==================== STAFF/ADMIN: APPROVE CANCELLATION ====================
class ApproveCancellationView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrStaff]

    def post(self, request, request_id):
        cancellation_request = get_object_or_404(CancellationRequest, id=request_id)
        
        if cancellation_request.status != 'pending':
            return Response(
                {'error': f'This request is already {cancellation_request.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking_models = {
            'room': Booking,
            'table': TableBooking,
            'conference': ConferenceBooking,
            'venue': VenueBooking,
        }

        if cancellation_request.booking_type not in booking_models:
            return Response(
                {'error': 'Invalid booking type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        model_class = booking_models[cancellation_request.booking_type]
        
        try:
            booking = model_class.objects.get(id=cancellation_request.booking_id)
        except model_class.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        refund_amount = booking.total_price if booking.status != 'checked_in' else 0

        refund = Refund.objects.create(
            cancellation_request=cancellation_request,
            booking_id=booking.id,
            booking_type=cancellation_request.booking_type,
            amount=refund_amount,
            phone_number=request.user.profile.phone if hasattr(request.user, 'profile') else '',
            status='pending',
            processed_by=request.user
        )

        cancellation_request.status = 'approved'
        cancellation_request.approved_by = request.user
        cancellation_request.approved_at = timezone.now()
        cancellation_request.refund_amount = refund_amount
        cancellation_request.staff_notes = request.data.get('staff_notes', '')
        cancellation_request.save()

        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        if refund_amount > 0:
            booking.payment_status = 'refund_pending'
        booking.save()

        return Response({
            'message': 'Cancellation approved',
            'refund_amount': str(refund_amount),
            'refund_id': refund.id,
            'booking_id': booking.id,
            'booking_type': cancellation_request.booking_type
        })


### ==================== STAFF/ADMIN: REJECT CANCELLATION ====================
class RejectCancellationView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrStaff]

    def post(self, request, request_id):
        cancellation_request = get_object_or_404(CancellationRequest, id=request_id)
        
        if cancellation_request.status != 'pending':
            return Response(
                {'error': f'This request is already {cancellation_request.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking_models = {
            'room': Booking,
            'table': TableBooking,
            'conference': ConferenceBooking,
            'venue': VenueBooking,
        }

        if cancellation_request.booking_type not in booking_models:
            return Response(
                {'error': 'Invalid booking type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        model_class = booking_models[cancellation_request.booking_type]
        
        try:
            booking = model_class.objects.get(id=cancellation_request.booking_id)
        except model_class.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        cancellation_request.status = 'rejected'
        cancellation_request.staff_notes = request.data.get('staff_notes', '')
        cancellation_request.save()

        booking.status = 'confirmed'
        booking.cancellation_reason = None
        booking.save()

        return Response({
            'message': 'Cancellation rejected',
            'booking_id': booking.id,
            'booking_type': cancellation_request.booking_type,
            'status': 'rejected'
        })


### ==================== STAFF/ADMIN: PROCESS REFUND ====================
class ProcessRefundView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrStaff]

    def post(self, request, refund_id):
        refund = get_object_or_404(Refund, id=refund_id)
        
        if refund.status != 'pending':
            return Response(
                {'error': f'Refund is already {refund.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        refund.status = 'processing'
        refund.save()

        transaction_id = f"REF-{refund.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        refund.status = 'completed'
        refund.transaction_id = transaction_id
        refund.save()

        booking_models = {
            'room': Booking,
            'table': TableBooking,
            'conference': ConferenceBooking,
            'venue': VenueBooking,
        }

        if refund.booking_type in booking_models:
            try:
                booking = booking_models[refund.booking_type].objects.get(id=refund.booking_id)
                booking.payment_status = 'refunded'
                booking.save()
            except:
                pass

        return Response({
            'message': 'Refund processed successfully',
            'refund_id': refund.id,
            'transaction_id': transaction_id,
            'amount': str(refund.amount),
            'status': 'completed'
        })


### ==================== GET REFUND BY REQUEST (NEW) ====================
class GetRefundByRequestView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrStaff]

    def get(self, request, request_id):
        try:
            refund = Refund.objects.get(cancellation_request_id=request_id)
            return Response({
                'id': refund.id,
                'status': refund.status,
                'amount': refund.amount,
                'booking_id': refund.booking_id,
                'booking_type': refund.booking_type,
                'created_at': refund.created_at,
                'processed_by': refund.processed_by.username if refund.processed_by else None,
            })
        except Refund.DoesNotExist:
            return Response(
                {'error': 'Refund not found for this request'},
                status=status.HTTP_404_NOT_FOUND
            )