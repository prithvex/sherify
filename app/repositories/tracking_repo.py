from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tracking import TrackingEvent, WebhookEvent


class TrackingRepository:
    async def create_tracking_event(
        self,
        db: AsyncSession,
        event: TrackingEvent,
    ) -> TrackingEvent:
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    async def list_by_recipient(
        self,
        db: AsyncSession,
        recipient_id: UUID,
    ) -> List[TrackingEvent]:
        stmt = (
            select(TrackingEvent)
            .where(TrackingEvent.campaign_recipient_id == recipient_id)
            .order_by(TrackingEvent.created_at.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_webhook_event_by_provider_id(
        self,
        db: AsyncSession,
        provider: str,
        provider_event_id: str,
    ) -> Optional[WebhookEvent]:
        stmt = select(WebhookEvent).where(
            WebhookEvent.provider == provider,
            WebhookEvent.provider_event_id == provider_event_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_webhook_event_by_id(
        self,
        db: AsyncSession,
        webhook_event_id: UUID,
    ) -> Optional[WebhookEvent]:
        stmt = select(WebhookEvent).where(WebhookEvent.id == webhook_event_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_webhook_event(
        self,
        db: AsyncSession,
        event: WebhookEvent,
    ) -> WebhookEvent:
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    async def update_webhook_event(
        self,
        db: AsyncSession,
        event: WebhookEvent,
    ) -> WebhookEvent:
        await db.commit()
        await db.refresh(event)
        return event


tracking_repository = TrackingRepository()
