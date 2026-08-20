import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from app.models.base import Base, CreatedAtMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.campaign import EmailCampaign
    from app.models.recipient import CampaignRecipient


class TrackingEvent(Base, UUIDMixin, CreatedAtMixin):
    """
    Immutable historical record of a recipient engagement or delivery event (OPENED, BOUNCED).
    """
    __tablename__ = "tracking_events"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaign_recipients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    provider_event_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    campaign: Mapped["EmailCampaign"] = relationship(
        "EmailCampaign",
    )
    recipient: Mapped["CampaignRecipient"] = relationship(
        "CampaignRecipient",
        back_populates="tracking_events",
    )


class WebhookEvent(Base, UUIDMixin, TimestampMixin):
    """
    Persistent log of incoming provider webhook dispatches, tracking deduplication and processing state.
    """
    __tablename__ = "webhook_events"

    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_webhook_provider_event"),
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    provider_event_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    payload_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        server_default=text("'{}'::json"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="received",
        nullable=False,
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
