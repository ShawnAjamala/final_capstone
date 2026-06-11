import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import MpesaTransaction, Booking
from .mpesa import initiate_stk_push

logger = logging.getLogger(__name__)


### ==================== INITIATE M-PESA PAYMENT ====================
# Sends STK Push to customer's phone.
# Accepts optional booking_id — auto-formats reference as "BK-{id}".
# This links the payment to the booking for auto-confirmation in the callback.
@csrf_exempt
@require_POST
def initiate_payment(request):
    try:
        body         = json.loads(request.body)
        phone_number = body.get("phone_number", "").strip()
        amount       = body.get("amount")
        reference    = body.get("reference", "HotelBooking")
        description  = body.get("description", "Hotel Booking Payment")
        booking_id   = body.get("booking_id")

        if not phone_number or not amount:
            return JsonResponse({"error": "phone_number and amount are required."}, status=400)

        # If booking_id is provided, format reference as BK-{id}
        if booking_id:
            reference = f"BK-{booking_id}"

        daraja_response = initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=reference,
            transaction_desc=description,
        )

        if daraja_response.get("ResponseCode") == "0":
            checkout_request_id = daraja_response["CheckoutRequestID"]
            MpesaTransaction.objects.create(
                checkout_request_id=checkout_request_id,
                phone_number=phone_number,
                amount=amount,
                reference=reference,
                description=description,
                status="Pending",
            )
            return JsonResponse({
                "status":              "pending",
                "message":             "STK Push sent. Check your phone.",
                "checkout_request_id": checkout_request_id,
                "reference":           reference,
            })

        return JsonResponse({
            "status":  "error",
            "message": daraja_response.get("errorMessage", "Unknown error from Daraja."),
        }, status=502)

    except Exception as e:
        logger.exception("STK Push failed")
        return JsonResponse({"error": str(e)}, status=500)


### ==================== M-PESA CALLBACK (PAYMENT RESULT) ====================
# Called by Safaricom with the actual payment result.
# On success: marks transaction Completed + auto-confirms the linked booking.
# Reference "BK-{id}" is used to find the booking.
@csrf_exempt
@require_POST
def mpesa_callback(request):
    try:
        data = json.loads(request.body)
        stk  = data.get("Body", {}).get("stkCallback", {})

        checkout_request_id = stk.get("CheckoutRequestID")
        result_code         = stk.get("ResultCode")
        result_desc         = stk.get("ResultDesc", "")

        try:
            transaction = MpesaTransaction.objects.get(checkout_request_id=checkout_request_id)
        except MpesaTransaction.DoesNotExist:
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

        if result_code == 0:
            # Payment successful
            items = stk.get("CallbackMetadata", {}).get("Item", [])
            meta  = {item["Name"]: item.get("Value") for item in items}
            transaction.status        = "Completed"
            transaction.mpesa_receipt = meta.get("MpesaReceiptNumber", "")
            transaction.result_desc   = result_desc
            transaction.save()

            # Auto-confirm the booking linked to this payment
            _confirm_booking(transaction)

        elif result_code == 1032:
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
@csrf_exempt
def payment_status(request, checkout_request_id):
    try:
        tx = MpesaTransaction.objects.get(checkout_request_id=checkout_request_id)
        return JsonResponse({
            "status":        tx.status,
            "mpesa_receipt": tx.mpesa_receipt,
            "result_desc":   tx.result_desc,
            "amount":        str(tx.amount),
            "phone_number":  tx.phone_number,
            "reference":     tx.reference,
        })
    except MpesaTransaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found."}, status=404)


### ==================== HELPER: CONFIRM BOOKING AFTER PAYMENT ====================
# Extracts booking ID from transaction reference (format: "BK-123")
# Updates booking to confirmed + paid.
def _confirm_booking(transaction):
    reference = transaction.reference

    if reference and reference.startswith("BK-"):
        try:
            booking_id = reference.replace("BK-", "").strip()
            booking = Booking.objects.get(id=booking_id)
            booking.status = 'confirmed'
            booking.payment_status = 'paid'
            booking.mpesa_transaction = transaction
            booking.save()
            logger.info(f"Booking #{booking.id} confirmed via M-Pesa payment")
        except (ValueError, Booking.DoesNotExist):
            logger.warning(f"No booking found for reference: {reference}")