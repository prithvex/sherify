import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.template import EmailTemplate
    from app.models.contact_list import ContactList
    from app.models.recipient import CampaignRecipient


class EmailCampaign(Base, UUIDMixin, TimestampMixin):
    """
    EmailCampaign entity representing a marketing campaign.
    """
    __tablename__ = "email_campaigns"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    contact_list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contact_lists.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False,
        index=True,
    )

    # V6 Scheduling and Sender Identity fields
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    timezone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    from_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    from_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    reply_to: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
    )
    template: Mapped["EmailTemplate"] = relationship(
        "EmailTemplate",
        back_populates="campaigns",
    )
    contact_list: Mapped["ContactList"] = relationship(
        "ContactList",
    )
    recipients: Mapped[List["CampaignRecipient"]] = relationship(
        "CampaignRecipient",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )
