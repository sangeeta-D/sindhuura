from celery import shared_task
from django.utils import timezone

from .models import SubscriptionPayment


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def expire_subscriptions(self):
    now = timezone.now()

    expired_payments = SubscriptionPayment.objects.filter(
        payment_status="success",
        expires_at__isnull=False,
        expires_at__lt=now,
        user__is_premium=True
    ).select_related("user")

    expired_users = set()

    for payment in expired_payments:
        payment.payment_status = "refunded"  # or "expired" (better – see note)
        payment.save(update_fields=["payment_status"])

        expired_users.add(payment.user)

    # Update users in bulk
    for user in expired_users:
        user.is_premium = False
        user.save(update_fields=["is_premium"])

    return f"Expired {len(expired_users)} subscriptions"
