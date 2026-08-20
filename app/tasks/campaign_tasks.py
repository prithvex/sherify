import asyncio
import logging
from uuid import UUID
from celery.utils.log import get_task_logger
from app.tasks.celery_app import celery_app

logger = get_task_logger(__name__)


class TransientCampaignError(Exception):
    """Raised when a transient provider or network failure should trigger Celery backoff retry."""
    pass


@celery_app.task(
    bind=True,
    name="app.tasks.campaign_tasks.execute_campaign_task",
    max_retries=5,
    default_retry_delay=5,
)
def execute_campaign_task(self, campaign_id: str):
    """
    Celery task that orchestrates background batch execution of a queued email campaign.
    """
    logger.info(f"[Task {self.request.id}] Starting execution for Campaign ID: {campaign_id}")
    from app.services.campaign_execution_service import campaign_execution_service

    try:
        # Run async campaign execution in an event loop
        asyncio.run(
            campaign_execution_service.execute_campaign(
                campaign_id=UUID(campaign_id),
                task_id=self.request.id,
            )
        )
        logger.info(f"[Task {self.request.id}] Finished execution for Campaign ID: {campaign_id}")
    except TransientCampaignError as exc:
        retry_count = self.request.retries
        countdown = min(2 ** retry_count * 5, 120)
        logger.warning(
            f"[Task {self.request.id}] Transient error for Campaign ID {campaign_id}: {exc}. "
            f"Retrying in {countdown}s (Attempt {retry_count + 1}/5)..."
        )
        raise self.retry(exc=exc, countdown=countdown)
    except Exception as exc:
        logger.error(
            f"[Task {self.request.id}] Unhandled error for Campaign ID {campaign_id}: {exc}",
            exc_info=True,
        )
        raise exc


@celery_app.task(
    name="app.tasks.campaign_tasks.check_scheduled_campaigns_task",
)
def check_scheduled_campaigns_task():
    """
    Periodic Celery Beat task that triggers due scheduled campaigns.
    """
    from app.core.database import AsyncSessionLocal
    from app.services.campaign_service import campaign_service

    async def _run():
        async with AsyncSessionLocal() as session:
            count = await campaign_service.trigger_due_scheduled_campaigns(session)
            if count > 0:
                logger.info(f"Celery Beat check triggered {count} due scheduled campaigns.")

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Error checking scheduled campaigns in Celery Beat: {exc}", exc_info=True)
