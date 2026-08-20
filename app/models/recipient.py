import secrets
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.campaign import EmailCampaign
    from app.models.subscriber import Subscriber
    from app.models.tracking import TrackingEvent


def generate_tracking_token() -> str:
    return secrets.token_urlsafe(32)


class CampaignRecipient(Base, UUIDMixin, TimestampMixin):
    """
    CampaignRecipient represents the immutable snapshot execution record of
    an email delivery attempt for one subscriber in a campaign.
    """
    __tablename__ = "campaign_recipients"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscriber_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscribers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    tracking_token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        default=generate_tracking_token,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    provider_message_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    failed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    opened_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    bounced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint("campaign_id", "email", name="uq_campaign_recipient_email"),
    )

    # Relationships
    campaign: Mapped["EmailCampaign"] = relationship(
        "EmailCampaign",
        back_populates="recipients",
    )
    subscriber: Mapped[Optional["Subscriber"]] = relationship(
        "Subscriber",
    )
    tracking_events: Mapped[List["TrackingEvent"]] = relationship(
        "TrackingEvent",
        back_populates="recipient",
        cascade="all, delete-orphan",
    )
