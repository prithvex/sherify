from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tracking import TrackingEvent
from app.repositories.recipient_repo import recipient_repository

# Standard 1x1 transparent GIF (43 bytes)
TRANSPARENT_GIF_BYTES = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


class TrackingService:
    """
    Public open tracking service recording recipient engagement idempotently.
    """

    async def record_open(
        self,
        db: AsyncSession,
        tracking_token: str,
    ) -> bytes:
        recipient = await recipient_repository.get_by_tracking_token(db, tracking_token=tracking_token)
        if not recipient:
            # Return transparent GIF silently without exposing invalid token status
            return TRANSPARENT_GIF_BYTES

        now_ts = datetime.now(timezone.utc)

        # Idempotent first-open recording
        if recipient.opened_at is None:
            recipient.opened_at = now_ts

            tracking_event = TrackingEvent(
                campaign_id=recipient.campaign_id,
                campaign_recipient_id=recipient.id,
                event_type="opened",
                occurred_at=now_ts,
                received_at=now_ts,
                provider_event_id=None,
            )
            db.add(tracking_event)
            await db.commit()

        return TRANSPARENT_GIF_BYTES


tracking_service = TrackingService()
