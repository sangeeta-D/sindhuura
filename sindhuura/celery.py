from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "expire-subscriptions-daily": {
        "task": "subscriptions.tasks.expire_subscriptions",
        "schedule": crontab(hour=0, minute=5),  # every day at 12:05 AM
    },
}
