import asyncio
import logging
from uuid import UUID
from celery.utils.log import get_task_logger
from app.tasks.celery_app import celery_app

logger = get_task_logger(__name__)


class TransientImportError(Exception):
    """Raised when a transient database or storage failure should trigger Celery backoff retry."""
    pass


@celery_app.task(
    bind=True,
    name="app.tasks.import_tasks.process_subscriber_import",
    max_retries=3,
    default_retry_delay=10,
)
def process_subscriber_import(self, import_job_id: str):
    """
    Celery task that streams, validates, and batch-imports subscribers from an uploaded CSV file.
    """
    logger.info(f"[Task {self.request.id}] Starting CSV subscriber import for Job ID: {import_job_id}")
    from app.services.import_execution_service import import_execution_service

    try:
        asyncio.run(
            import_execution_service.execute_import(
                job_id=UUID(import_job_id),
                task_id=self.request.id,
            )
        )
        logger.info(f"[Task {self.request.id}] Finished CSV subscriber import for Job ID: {import_job_id}")
    except TransientImportError as exc:
        retry_count = self.request.retries
        countdown = min(2 ** retry_count * 10, 120)
        logger.warning(
            f"[Task {self.request.id}] Transient error for Import Job {import_job_id}: {exc}. "
            f"Retrying in {countdown}s (Attempt {retry_count + 1}/3)..."
        )
        raise self.retry(exc=exc, countdown=countdown)
    except Exception as exc:
        logger.error(
            f"[Task {self.request.id}] Unhandled error for Import Job {import_job_id}: {exc}",
            exc_info=True,
        )
        raise exc
