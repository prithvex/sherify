import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.tracking import TrackingEvent
from app.repositories.recipient_repo import recipient_repository
from app.repositories.tracking_repo import tracking_repository
from app.webhooks import get_webhook_parser

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _get_session(db: Optional[AsyncSession] = None) -> AsyncGenerator[AsyncSession, None]:
    if db is not None:
        yield db
    else:
        async with AsyncSessionLocal() as session:
            yield session


class WebhookExecutionService:
    """
    Worker execution service that processes WebhookEvents asynchronously and updates recipient history.
    """

    async def execute_webhook(
        self,
        webhook_event_id: UUID,
        task_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> None:
        async with _get_session(db) as session:
            event = await tracking_repository.get_webhook_event_by_id(session, webhook_event_id=webhook_event_id)
            if not event:
                logger.error(f"[Task {task_id}] WebhookEvent {webhook_event_id} not found.")
                return

            if event.status in ["processed", "ignored"]:
                logger.info(f"[Task {task_id}] WebhookEvent {webhook_event_id} already in terminal status '{event.status}'.")
                return

            # Mark PROCESSING
            event.status = "processing"
            await session.commit()

            # Parse Normalized Event
            parser = get_webhook_parser(event.provider)
            normalized = parser.parse_event(raw_body=b"", payload_json=event.payload_json)

            # Handle unsupported events
            if normalized.event_type == "unsupported":
                event.status = "ignored"
                event.error_message = f"Unsupported event type: '{event.event_type}'"
                event.processed_at = datetime.now(timezone.utc)
                await session.commit()
                logger.info(f"[Task {task_id}] WebhookEvent {webhook_event_id} ignored (unsupported event type).")
                return

            # Match recipient by provider_message_id
            recipient = None
            if normalized.provider_message_id:
                recipient = await recipient_repository.get_by_provider_message_id(
                    session,
                    provider_message_id=normalized.provider_message_id,
                )

            if not recipient:
                event.status = "ignored"
                event.error_message = f"No recipient found for provider message ID '{normalized.provider_message_id}'"
                event.processed_at = datetime.now(timezone.utc)
                await session.commit()
                logger.warning(f"[Task {task_id}] WebhookEvent {webhook_event_id} ignored (unresolved message ID: {normalized.provider_message_id}).")
                return

            now_ts = datetime.now(timezone.utc)

            # Process BOUNCE
            if normalized.event_type == "bounced":
                # Update recipient status to bounced if it was previously sent
                if recipient.status == "sent":
                    recipient.status = "bounced"
                
                if recipient.bounced_at is None:
                    recipient.bounced_at = normalized.occurred_at or now_ts

                # Create TrackingEvent
                tracking_event = TrackingEvent(
                    campaign_id=recipient.campaign_id,
                    campaign_recipient_id=recipient.id,
                    event_type="bounced",
                    occurred_at=normalized.occurred_at or now_ts,
                    received_at=now_ts,
                    provider_event_id=normalized.provider_event_id,
                )
                session.add(tracking_event)

            # Process OPEN (if dispatched via webhook)
            elif normalized.event_type == "opened":
                if recipient.opened_at is None:
                    recipient.opened_at = normalized.occurred_at or now_ts
                
                tracking_event = TrackingEvent(
                    campaign_id=recipient.campaign_id,
                    campaign_recipient_id=recipient.id,
                    event_type="opened",
                    occurred_at=normalized.occurred_at or now_ts,
                    received_at=now_ts,
                    provider_event_id=normalized.provider_event_id,
                )
                session.add(tracking_event)

            event.status = "processed"
            event.processed_at = now_ts
            await session.commit()
            logger.info(f"[Task {task_id}] WebhookEvent {webhook_event_id} processed successfully for recipient {recipient.id}.")


webhook_execution_service = WebhookExecutionService()
