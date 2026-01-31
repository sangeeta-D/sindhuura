# auth_api/utils/sms.py
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def send_sms_otp(phone_number, otp):
    """
    Send OTP via MySMSMantra using correct API endpoint
    """
    print("=" * 50)
    print("📱 SMS OTP SEND FUNCTION CALLED")
    print("=" * 50)
    
    mobile = phone_number[-10:] if len(phone_number) > 10 else phone_number
    
    print(f"📞 Original Phone: {phone_number}")
    print(f"📞 Formatted Mobile: {mobile}")
    print(f"🔢 OTP: {otp}")
    
    # Correct API endpoint
    url = "https://api.mylogin.co.in/api/v2/SendSMS"
    
    # Template: Dear User, Your SINDHUURA Verification Code is {#var#}
    message = f"Dear User, Your SINDHUURA Verification Code is {otp}"
    
    params = {
        "SenderId": settings.MYSMSMANTRA_SENDER_ID,
        "Message": message,
        "MobileNumbers": mobile,
        "ApiKey": settings.MYSMSMANTRA_API_KEY,
        "ClientId": settings.MYSMSMANTRA_CLIENT_ID,
        "DLTTemplateId": settings.MYSMSMANTRA_DLT_TEMPLATE_ID,
    }
    
    print("\n🔧 Request Details:")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print()

    # 🚨 DEBUGGING: Check if this is a test environment
    if getattr(settings, 'DEBUG', False):
        print("⚠️  DEBUG MODE: Simulating SMS send (not actually sending)")
        print(f"📱 Would send to: {mobile}")
        print(f"💬 Message: {message}")
        # For testing OTP functionality, you can temporarily enable actual sending
        # return True  # Comment this line to actually send SMS in debug mode
        # Uncomment the lines below to actually send SMS even in debug mode

    try:
        print("🚀 Sending HTTP GET request...")
        response = requests.get(url, params=params, timeout=10)
        
        print(f"✅ Response Received!")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Body: {response.text}")
        print()
        
        # Parse JSON response
        try:
            response_data = response.json()
            print(f"🔍 Parsed Response: {response_data}")
            
            # Check for success based on MySMSMantra API response format
            error_code = response_data.get('ErrorCode', -1)
            if error_code == 0 or error_code == "0":
                # Check individual message status if Data array exists
                data = response_data.get('Data', [])
                if data:
                    for msg in data:
                        msg_error_code = msg.get('MessageErrorCode', -1)
                        if msg_error_code != 0 and msg_error_code != "0":
                            print(f"❌ Message failed: {msg.get('MessageErrorDescription', 'Unknown error')}")
                            return False
                print("✅ SMS sent successfully")
                is_success = True
            else:
                print(f"❌ API Error: {response_data.get('ErrorDescription', 'Unknown error')}")
                is_success = False
                
        except ValueError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            # Fallback to status code check
            is_success = response.status_code == 200
        
        logger.info(f"SMS sent to {phone_number}")
        logger.info(f"Response: {response.status_code} - {response.text}")
        
        print(f"🎯 Success Check: {is_success}")
        print("=" * 50)
        
        return is_success
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
        logger.error(f"SMS error: {str(e)}")
        return False