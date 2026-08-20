from celery import Celery
from kombu import Queue
from app.core.config import settings

celery_app = Celery(
    "sherify_campaign_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.campaign_tasks",
        "app.tasks.import_tasks",
        "app.tasks.webhook_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="campaigns",
    task_queues=(
        Queue("campaigns", routing_key="campaigns.#"),
        Queue("imports", routing_key="imports.#"),
        Queue("webhooks", routing_key="webhooks.#"),
        Queue("scheduler", routing_key="scheduler.#"),
    ),
    task_routes={
        "app.tasks.campaign_tasks.execute_campaign_task": {"queue": "campaigns"},
        "app.tasks.campaign_tasks.check_scheduled_campaigns_task": {"queue": "scheduler"},
        "app.tasks.import_tasks.process_subscriber_import": {"queue": "imports"},
        "app.tasks.webhook_tasks.process_webhook_event": {"queue": "webhooks"},
    },
    beat_schedule={
        "check-scheduled-campaigns-every-30-seconds": {
            "task": "app.tasks.campaign_tasks.check_scheduled_campaigns_task",
            "schedule": 30.0,
            "options": {"queue": "scheduler"},
        },
    },
)
