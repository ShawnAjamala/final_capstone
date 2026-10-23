import base64
import requests
from datetime import datetime
from decouple import config


MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"
MPESA_CALLBACK_URL = "https://final-capstone-lt3j.onrender.com/api/mpesa/callback/"


def get_access_token():
    consumer_key = config("MPESA_CONSUMER_KEY")
    consumer_secret = config("MPESA_CONSUMER_SECRET")

    url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(
        url,
        auth=(consumer_key, consumer_secret),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def initiate_stk_push(phone_number, amount, account_reference, transaction_desc):
    """
    Triggers an STK Push to the customer's phone.
    Returns the full Daraja response dict.
    """
    access_token = get_access_token()

    shortcode = config("MPESA_SHORTCODE")
    passkey = config("MPESA_PASSKEY")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        f"{shortcode}{passkey}{timestamp}".encode()
    ).decode()

    # Normalise phone: 0712345678 → 254712345678
    phone = str(phone_number).strip()
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("+"):
        phone = phone[1:]

    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),          # Daraja rejects decimals
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc,
    }

    url = f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def query_stk_push(checkout_request_id):
    """Verify the final status of an STK push directly with Daraja."""
    access_token = get_access_token()
    shortcode = config("MPESA_SHORTCODE")
    passkey = config("MPESA_PASSKEY")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        f"{shortcode}{passkey}{timestamp}".encode()
    ).decode()

    response = requests.post(
        f"{MPESA_BASE_URL}/mpesa/stkpushquery/v1/query",
        json={
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        },
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()