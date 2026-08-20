import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.contact_list import ContactList


class Subscriber(Base, UUIDMixin, TimestampMixin):
    """
    Subscriber entity representing an email contact within a ContactList.
    """
    __tablename__ = "subscribers"

    __table_args__ = (
        UniqueConstraint("contact_list_id", "email", name="uq_subscriber_contact_list_email"),
        Index("ix_subscribers_contact_list_status", "contact_list_id", "status"),
    )

    contact_list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contact_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    first_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False,
        index=True,
    )
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        default=dict,
        server_default=text("'{}'::json"),
        nullable=False,
    )

    # Relationships
    contact_list: Mapped["ContactList"] = relationship(
        "ContactList",
        back_populates="subscribers",
    )
