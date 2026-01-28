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
        return

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        data=data or {},
    )

    try:
        messaging.send(message)
    except Exception as e:
        print("🔥 Firebase error:", e)
