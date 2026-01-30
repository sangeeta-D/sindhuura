import firebase_admin
from firebase_admin import credentials, messaging
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cred_path = os.path.join(BASE_DIR, "chat", "sindhuura-fb.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)


def send_push_notification(token, title, body, data=None):
    if not token:
        print("🔥 No FCM token provided, skipping notification")
        return

    print(f"🔥 Sending FCM notification to token: {token[:10]}..., title: {title}")

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        data=data or {},
    )

    try:
        response = messaging.send(message)
        print(f"🔥 FCM notification sent successfully, message ID: {response}")
    except Exception as e:
        print("🔥 Firebase error:", e)
