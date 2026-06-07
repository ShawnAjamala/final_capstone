# mpesa.py
import base64
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth
from decouple import config

# Sandbox base URL. For production, swap to https://api.safaricom.co.ke
BASE_URL = "https://sandbox.safaricom.co.ke"


def get_access_token():
    """Authenticate with Daraja and return a short-lived access token."""
    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(
        url,
        auth=HTTPBasicAuth(
            config("MPESA_CONSUMER_KEY"),
            config("MPESA_CONSUMER_SECRET"),
        ),
    )
    response.raise_for_status()
    return response.json()["access_token"]