# auth_api/utils/sms.py
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def send_sms_otp(phone_number, otp):
    """
    Send OTP via MyLogin SendSMS API (v2) – Documentation compliant
    """

    mobile = phone_number[-10:] if len(phone_number) > 10 else phone_number

    url = "https://api.mylogin.co.in/api/v2/SendSMS"

    message = f"Dear User, Your SINDHUURA Verification Code is {otp}"

    payload = {
        "SenderId": settings.MYSMSMANTRA_SENDER_ID,
        "Message": message,
        "MobileNumbers": mobile,
        "ApiKey": settings.MYSMSMANTRA_API_KEY,
        "ClientId": settings.MYSMSMANTRA_CLIENT_ID,

        # Optional but recommended
        "Is_Unicode": False,
        "Is_Flash": False,
        "IsRegisteredForDelivery": True,
        "DataCoding": "00",   # GSM default
        "GroupId": ""
    }

    headers = {
        "Content-Type": "application/json",
        "Type": "json"
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )

        logger.info(f"SMS API Status: {response.status_code}")
        logger.info(f"SMS API Response: {response.text}")

        if response.status_code != 200:
            return False

        try:
            data = response.json()
        except ValueError:
            return False

        # MyLogin success condition
        if str(data.get("ErrorCode")) == "0":
            return True

        logger.error(f"SMS failed: {data.get('ErrorDescription')}")
        return False

    except Exception as e:
        logger.exception("SMS sending failed")
        return False