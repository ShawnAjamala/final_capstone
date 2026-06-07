import base64
import requests
from datetime import datetime
from decouple import config


MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"


def get_access_token():
    consumer_key = config("MPESA_CONSUMER_KEY")
    consumer_secret = config("MPESA_CONSUMER_SECRET")

    url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(consumer_key, consumer_secret))
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
    callback_url = config("MPESA_CALLBACK_URL")

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
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc,
    }

    url = f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()