from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tracking import WebhookEvent
from app.repositories.tracking_repo import tracking_repository
from app.schemas.tracking import WebhookIngestResponse
from app.tasks.webhook_tasks import process_webhook_event
from app.webhooks import get_webhook_parser, get_webhook_verifier


class WebhookService:
    """
    Public webhook ingestion service verifying provider signatures and enqueuing asynchronous processing.
    """

    async def ingest_webhook(
        self,
        db: AsyncSession,
        provider: str,
        raw_body: bytes,
        headers: Dict[str, str],
        payload_json: Dict[str, Any],
    ) -> WebhookIngestResponse:
        # 1. Verify Webhook Signature
        verifier = get_webhook_verifier(provider)
        is_valid = await verifier.verify_signature(raw_body=raw_body, headers=headers)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

        # 2. Parse & Normalize Event
        parser = get_webhook_parser(provider)
        normalized = parser.parse_event(raw_body=raw_body, payload_json=payload_json)

        # 3. Webhook Deduplication Check
        existing_event = await tracking_repository.get_webhook_event_by_provider_id(
            db,
            provider=normalized.provider,
            provider_event_id=normalized.provider_event_id,
        )
        if existing_event:
            return WebhookIngestResponse(
                event_id=existing_event.id,
                status=existing_event.status,
                message="Webhook event already received",
            )

        # 4. Persist WebhookEvent record
        event = WebhookEvent(
            provider=normalized.provider,
            provider_event_id=normalized.provider_event_id,
            event_type=normalized.event_type,
            payload_json=payload_json,
            status="received",
            received_at=datetime.now(timezone.utc),
        )
        created_event = await tracking_repository.create_webhook_event(db, event)

        # 5. Enqueue Celery processing task
        try:
            process_webhook_event.delay(str(created_event.id))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Background task broker is currently unavailable.",
            )

        return WebhookIngestResponse(
            event_id=created_event.id,
            status=created_event.status,
            message="Webhook event received and queued",
        )


webhook_service = WebhookService()
