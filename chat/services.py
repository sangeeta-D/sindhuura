from auth_api.models import SubscriptionPayment

def is_user_subscribed(user):
    return SubscriptionPayment.objects.filter(
        user=user,
        payment_status="success"
    ).exists()


def can_send_message(sender, receiver, message_type):
    sender_subscribed = is_user_subscribed(sender)
    receiver_subscribed = is_user_subscribed(receiver)

    # Case 1: Non-subscriber → Subscriber
    if not sender_subscribed and receiver_subscribed:
        return False, "Upgrade your plan to start conversation"

    # Case 2: Subscriber → Non-subscriber
    if sender_subscribed and not receiver_subscribed:
        return False, "User has not upgraded their plan"

    # Case 3: Non-subscriber → Non-subscriber
    if not sender_subscribed and not receiver_subscribed:
        if message_type != "predefined":
            return False, "Only predefined messages are allowed"
        return True, None

    # Case 4: Subscriber → Subscriber
    if sender_subscribed and receiver_subscribed:
        return True, None

    return False, "Chat not allowed"
