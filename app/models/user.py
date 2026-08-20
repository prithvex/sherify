from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.contact_list import ContactList


class User(Base, UUIDMixin, TimestampMixin):
    """
    User entity representing an account in Sherify.
    """
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    contact_lists: Mapped[List["ContactList"]] = relationship(
        "ContactList",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
