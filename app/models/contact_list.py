import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.subscriber import Subscriber


class ContactList(Base, UUIDMixin, TimestampMixin):
    """
    ContactList entity representing an audience group owned by a User.
    """
    __tablename__ = "contact_lists"

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
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="contact_lists",
    )
    subscribers: Mapped[List["Subscriber"]] = relationship(
        "Subscriber",
        back_populates="contact_list",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
