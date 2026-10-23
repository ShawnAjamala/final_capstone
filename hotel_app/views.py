import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from requests import RequestException
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import MpesaTransaction, Booking, TableBooking, ConferenceBooking, VenueBooking
from .mpesa import initiate_stk_push, query_stk_push
from .permissions import IsGuest

logger = logging.getLogger(__name__)

BOOKING_MODELS = {
    "BK": Booking,
    "TBL": TableBooking,
    "CONF": ConferenceBooking,
    "VEN": VenueBooking,
}


def get_booking_from_reference(reference):
    if not isinstance(reference, str):
        return None

    prefix, separator, booking_id = reference.partition("-")
    model = BOOKING_MODELS.get(prefix)
    if not separator or model is None or not booking_id.isdecimal():
        return None

    try:
        return model.objects.get(id=int(booking_id))
    except model.DoesNotExist:
        return None


### ==================== INITIATE M-PESA PAYMENT ====================
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsGuest])
def initiate_payment(request):
    phone_number = request.data.get("phone_number", "")
    reference = request.data.get("booking_id") or request.data.get("reference")

    if not isinstance(phone_number, str) or not phone_number.strip() or not reference:
        return Response(
            {"error": "phone_number and booking_id are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    booking = get_booking_from_reference(reference)
    if (
        booking is None
        or booking.guest_id != request.user.id
        or booking.status != "pending"
        or booking.payment_status != "unpaid"
    ):
        return Response(
            {"error": "A pending, unpaid booking belonging to you is required."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        daraja_response = initiate_stk_push(
            phone_number=phone_number.strip(),
            amount=booking.total_price,
            account_reference=reference,
            transaction_desc="Hotel booking payment",
        )
    except RequestException:
        logger.exception("STK Push failed for booking %s", reference)
        return Response(
            {"error": "Unable to initiate M-Pesa payment."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    if str(daraja_response.get("ResponseCode")) != "0":
        return Response(
            {
                "status": "error",
                "message": daraja_response.get(
                    "errorMessage", "Unable to initiate M-Pesa payment."
                ),
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    checkout_request_id = daraja_response.get("CheckoutRequestID")
    if not checkout_request_id:
        logger.error("Daraja accepted a payment request without a checkout ID")
        return Response(
            {"error": "Unable to initiate M-Pesa payment."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    MpesaTransaction.objects.create(
        checkout_request_id=checkout_request_id,
        phone_number=phone_number.strip(),
        amount=booking.total_price,
        reference=reference,
        description="Hotel booking payment",
        status="Pending",
    )
    return Response(
        {
            "status": "pending",
            "message": "STK Push sent. Check your phone.",
            "checkout_request_id": checkout_request_id,
            "reference": reference,
        },
        status=status.HTTP_201_CREATED,
    )


### ==================== M-PESA CALLBACK ====================
@csrf_exempt
@require_POST
def mpesa_callback(request):
    try:
        data = json.loads(request.body)
        stk  = data.get("Body", {}).get("stkCallback", {})

        checkout_request_id = stk.get("CheckoutRequestID")
        result_code         = stk.get("ResultCode")
        result_desc         = stk.get("ResultDesc", "")
        if checkout_request_id is None or result_code is None:
            logger.warning("Received an incomplete M-Pesa callback")
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

        try:
            transaction = MpesaTransaction.objects.get(checkout_request_id=checkout_request_id)
        except MpesaTransaction.DoesNotExist:
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
        if transaction.status != "Pending":
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

        verification = query_stk_push(checkout_request_id)
        verified_result = verification.get("ResultCode")
        if (
            str(verification.get("ResponseCode")) != "0"
            or str(verified_result) != str(result_code)
        ):
            logger.warning(
                "M-Pesa callback verification did not match transaction %s",
                checkout_request_id,
            )
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

        if str(result_code) == "0":
            items = stk.get("CallbackMetadata", {}).get("Item", [])
            meta  = {item["Name"]: item.get("Value") for item in items}
            transaction.status        = "Completed"
            transaction.mpesa_receipt = meta.get("MpesaReceiptNumber", "")
            transaction.result_desc   = result_desc
            transaction.save()

            _confirm_booking(transaction)

        elif str(result_code) == "1032":
            transaction.status      = "Cancelled"
            transaction.result_desc = result_desc
            transaction.save()
        else:
            transaction.status      = "Failed"
            transaction.result_desc = result_desc
            transaction.save()

    except Exception:
        logger.exception("Error processing M-Pesa callback")

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})


### ==================== CHECK PAYMENT STATUS ====================
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsGuest])
def payment_status(request, checkout_request_id):
    try:
        tx = MpesaTransaction.objects.get(checkout_request_id=checkout_request_id)
        booking = get_booking_from_reference(tx.reference)
        if booking is None or booking.guest_id != request.user.id:
            return Response({"error": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "status":        tx.status,
            "mpesa_receipt": tx.mpesa_receipt,
            "result_desc":   tx.result_desc,
            "amount":        str(tx.amount),
            "reference":     tx.reference,
        })
    except MpesaTransaction.DoesNotExist:
        return Response({"error": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)


### ==================== HELPER: CONFIRM ANY BOOKING TYPE ====================
def _confirm_booking(transaction):
    """
    Auto-confirms the booking linked to this payment.
    Supports: BK-{id}, TBL-{id}, CONF-{id}, VEN-{id}
    """
    reference = transaction.reference

    if not reference:
        return

    try:
        if reference.startswith("BK-"):
            booking_id = reference.replace("BK-", "").strip()
            booking = Booking.objects.get(id=booking_id)
            booking.status = 'confirmed'
            booking.payment_status = 'paid'
            booking.mpesa_transaction = transaction
            booking.save()
            logger.info(f"Room Booking #{booking.id} confirmed")

        elif reference.startswith("TBL-"):
            booking_id = reference.replace("TBL-", "").strip()
            booking = TableBooking.objects.get(id=booking_id)
            booking.status = 'confirmed'
            booking.payment_status = 'paid'
            booking.mpesa_transaction = transaction
            booking.save()
            logger.info(f"Table Booking #{booking.id} confirmed")

        elif reference.startswith("CONF-"):
            booking_id = reference.replace("CONF-", "").strip()
            booking = ConferenceBooking.objects.get(id=booking_id)
            booking.status = 'confirmed'
            booking.payment_status = 'paid'
            booking.mpesa_transaction = transaction
            booking.save()
            logger.info(f"Conference Booking #{booking.id} confirmed")

        elif reference.startswith("VEN-"):
            booking_id = reference.replace("VEN-", "").strip()
            booking = VenueBooking.objects.get(id=booking_id)
            booking.status = 'confirmed'
            booking.payment_status = 'paid'
            booking.mpesa_transaction = transaction
            booking.save()
            logger.info(f"Venue Booking #{booking.id} confirmed")

    except (ValueError, Booking.DoesNotExist, TableBooking.DoesNotExist, ConferenceBooking.DoesNotExist, VenueBooking.DoesNotExist):
        logger.warning(f"No booking found for reference: {reference}")