# auth_api/utils/sms.py

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms_otp(phone_number: str, otp: str) -> bool:
    """
    Send OTP using MyLogin SendSMS v2 API (DLT Template Based)
    Returns True if SMS sent successfully, else False.
    """

    try:
        # -----------------------------------------------------
        # 1️⃣ Ensure mobile number is in 91XXXXXXXXXX format
        # -----------------------------------------------------
        phone_number = phone_number.strip()

        if phone_number.startswith("+"):
            phone_number = phone_number[1:]

        if not phone_number.startswith("91"):
            mobile = f"91{phone_number[-10:]}"
        else:
            mobile = phone_number

        logger.info(f"Sending OTP to mobile: {mobile}")

        # -----------------------------------------------------
        # 2️⃣ Construct message matching DLT template
        # CRITICAL: Must match your registered template exactly
        # -----------------------------------------------------
        # Example template formats:
        # "{#var#} is your OTP for login. Valid for 5 minutes. Do not share with anyone."
        # "Your OTP is {#var#}. Please use it to verify your account."
        
        message = settings.MYSMSMANTRA_DLT_TEMPLATE_MESSAGE.format(otp=otp)
        
        logger.info(f"Message to send: {message}")

        # -----------------------------------------------------
        # 3️⃣ API URL
        # -----------------------------------------------------
        url = "https://api.mylogin.co.in/api/v2/SendSMS"

        # -----------------------------------------------------
        # 4️⃣ DLT Template Based Payload
        # -----------------------------------------------------
        payload = {
            "SenderId": settings.MYSMSMANTRA_SENDER_ID,
            "MobileNumbers": mobile,
            "ApiKey": settings.MYSMSMANTRA_API_KEY,
            "ClientId": settings.MYSMSMANTRA_CLIENT_ID,
            "TemplateId": settings.MYSMSMANTRA_DLT_TEMPLATE_ID,
            "Message": message,  # Full message with OTP inserted
            "Is_Unicode": False,
            "Is_Flash": False,
            "IsRegisteredForDelivery": True,
            "DataCoding": "00",
            "GroupId": ""
        }

        headers = {
            "Content-Type": "application/json",
            "Type": "json"
        }

        # -----------------------------------------------------
        # 5️⃣ Send Request
        # -----------------------------------------------------
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=15
        )

        logger.info(f"SMS API Status Code: {response.status_code}")
        logger.info(f"SMS API Raw Response: {response.text}")

        # -----------------------------------------------------
        # 6️⃣ Validate HTTP response
        # -----------------------------------------------------
        if response.status_code != 200:
            logger.error("SMS API returned non-200 response")
            return False

        # -----------------------------------------------------
        # 7️⃣ Parse JSON
        # -----------------------------------------------------
        try:
            data = response.json()
        except ValueError:
            logger.error("Invalid JSON response from SMS API")
            return False

        logger.info(f"SMS API Parsed Response: {data}")

        # -----------------------------------------------------
        # 8️⃣ Success Condition
        # -----------------------------------------------------
        if str(data.get("ErrorCode")) == "0":
            logger.info("OTP SMS sent successfully")
            return True

        logger.error(
            f"SMS sending failed | ErrorCode: {data.get('ErrorCode')} | "
            f"Description: {data.get('ErrorDescription')}"
        )
        return False

    except Exception as e:
        logger.exception("Exception occurred while sending OTP SMS")
        return False