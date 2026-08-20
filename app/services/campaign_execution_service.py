import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.rate_limiter import email_rate_limiter
from app.models.campaign import EmailCampaign
from app.models.recipient import CampaignRecipient
from app.providers import get_email_provider
from app.providers.base import EmailMessage
from app.repositories.campaign_repo import campaign_repository
from app.repositories.recipient_repo import recipient_repository
from app.repositories.template_repo import template_repository
from app.schemas.campaign import CampaignStatus
from app.schemas.recipient import RecipientStatus
from app.tasks.campaign_tasks import TransientCampaignError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _get_session(db: Optional[AsyncSession] = None) -> AsyncGenerator[AsyncSession, None]:
    if db is not None:
        yield db
    else:
        async with AsyncSessionLocal() as session:
            yield session


class CampaignExecutionService:
    """
    Service executing campaign batches in the background Celery worker with rate limiting,
    sender identity injection, and transient failure retries.
    """

    def _inject_tracking_pixel(self, html_content: Optional[str], tracking_token: Optional[str]) -> Optional[str]:
        if not html_content or not tracking_token:
            return html_content

        tracking_url = f"{settings.PUBLIC_API_BASE_URL.rstrip('/')}/track/open/{tracking_token}"
        pixel_tag = f'<img src="{tracking_url}" width="1" height="1" style="display:none" alt="" />'

        lower_html = html_content.lower()
        if "</body>" in lower_html:
            idx = lower_html.rfind("</body>")
            return html_content[:idx] + pixel_tag + html_content[idx:]
        return html_content + pixel_tag

    async def execute_campaign(
        self,
        campaign_id: UUID,
        task_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> None:
        """
        Idempotently process all pending recipients of a campaign in configurable batches,
        applying distributed rate limiting and sender configuration.
        """
        async with _get_session(db) as session:
            # 1. Fetch Campaign
            campaign = await campaign_repository.get_by_id(session, campaign_id=campaign_id)
            if not campaign:
                logger.error(f"[Task {task_id}] Campaign {campaign_id} not found.")
                return

            # If already finished or cancelled, skip
            if campaign.status in [
                CampaignStatus.COMPLETED.value,
                CampaignStatus.FAILED.value,
                CampaignStatus.CANCELLED.value,
            ]:
                logger.info(f"[Task {task_id}] Campaign {campaign_id} in terminal/cancelled status '{campaign.status}'. Aborting execution.")
                return

            # 2. Fetch Template Content
            template = await template_repository.get_by_id(session, template_id=campaign.template_id)
            if not template:
                logger.error(f"[Task {task_id}] Template {campaign.template_id} not found for Campaign {campaign_id}.")
                campaign.status = CampaignStatus.FAILED.value
                await session.commit()
                return

            # 3. Transition QUEUED / SCHEDULED -> SENDING
            if campaign.status in [CampaignStatus.QUEUED.value, CampaignStatus.SCHEDULED.value]:
                campaign.status = CampaignStatus.SENDING.value
                await session.commit()
                logger.info(f"[Task {task_id}] Campaign {campaign_id} transitioned to SENDING.")

            email_provider = get_email_provider()
            batch_size = settings.CAMPAIGN_BATCH_SIZE
            max_retries = settings.MAX_RECIPIENT_RETRIES
            has_transient_failure = False

            # Determine sender configuration (campaign override or global default)
            from_name = campaign.from_name or settings.EMAIL_FROM_NAME
            from_email = campaign.from_email or settings.EMAIL_FROM_ADDRESS
            reply_to = campaign.reply_to or settings.EMAIL_REPLY_TO

            # 4. Batch Processing Loop
            while True:
                # Check if campaign was cancelled during in-flight batch execution
                await session.refresh(campaign)
                if campaign.status == CampaignStatus.CANCELLED.value:
                    logger.warning(f"[Task {task_id}] Campaign {campaign_id} was cancelled during execution. Stopping further dispatches.")
                    break

                # Query next pending or stale processing recipients
                recipients = await recipient_repository.get_unprocessed_batch(
                    session,
                    campaign_id=campaign_id,
                    limit=batch_size,
                )
                if not recipients:
                    break

                # Mark batch as PROCESSING and increment attempts
                for r in recipients:
                    r.status = RecipientStatus.PROCESSING.value
                    r.attempts += 1
                await session.commit()

                # Dispatch emails for this batch with distributed rate limiting
                for recipient in recipients:
                    if recipient.status == RecipientStatus.SENT.value:
                        continue

                    # Distributed Rate Limiting Throttling
                    await email_rate_limiter.acquire(1)

                    # Inject tracking pixel into HTML
                    rendered_html = self._inject_tracking_pixel(
                        html_content=template.html_content,
                        tracking_token=recipient.tracking_token,
                    )

                    message = EmailMessage(
                        to_email=recipient.email,
                        subject=template.subject,
                        html_content=rendered_html,
                        text_content=template.text_content,
                        from_name=from_name,
                        from_email=from_email,
                        reply_to=reply_to,
                        metadata={"campaign_id": str(campaign_id), "recipient_id": str(recipient.id)},
                    )

                    try:
                        result = await email_provider.send_email(message)
                        now_utc = datetime.now(timezone.utc)

                        if result.success:
                            recipient.status = RecipientStatus.SENT.value
                            recipient.provider_message_id = result.provider_message_id
                            recipient.sent_at = now_utc
                            recipient.error_message = None
                        else:
                            if result.is_transient:
                                if recipient.attempts < max_retries:
                                    # Leave as pending for Celery backoff retry
                                    recipient.status = RecipientStatus.PENDING.value
                                    has_transient_failure = True
                                else:
                                    recipient.status = RecipientStatus.FAILED.value
                                    recipient.error_message = result.error_message or "Max retry attempts exceeded"
                                    recipient.failed_at = now_utc
                            else:
                                # Permanent failure
                                recipient.status = RecipientStatus.FAILED.value
                                recipient.error_message = result.error_message or "Permanent delivery failure"
                                recipient.failed_at = now_utc

                    except Exception as e:
                        logger.error(f"Error dispatching email to {recipient.email}: {e}")
                        recipient.status = RecipientStatus.FAILED.value
                        recipient.error_message = str(e)
                        recipient.failed_at = datetime.now(timezone.utc)

                # Commit batch updates to database
                await session.commit()

                # If transient failure occurred, trigger Celery task retry
                if has_transient_failure:
                    raise TransientCampaignError("Temporary email provider failure detected during batch dispatch.")

            # 5. Check Final Campaign State
            await session.refresh(campaign)
            if campaign.status != CampaignStatus.CANCELLED.value:
                unprocessed_count = await recipient_repository.count_unprocessed(session, campaign_id=campaign_id)
                if unprocessed_count == 0:
                    if campaign.status == CampaignStatus.SENDING.value:
                        campaign.status = CampaignStatus.COMPLETED.value
                        await session.commit()
                        logger.info(f"[Task {task_id}] Campaign {campaign_id} successfully COMPLETED.")


campaign_execution_service = CampaignExecutionService()
