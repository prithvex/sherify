import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.campaign import EmailCampaign


class EmailTemplate(Base, UUIDMixin, TimestampMixin):
    """
    EmailTemplate entity representing reusable email content and subject.
    """
    __tablename__ = "email_templates"

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
    html_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    text_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
    )
    campaigns: Mapped[List["EmailCampaign"]] = relationship(
        "EmailCampaign",
        back_populates="template",
    )
