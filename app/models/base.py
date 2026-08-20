import uuid
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for all SQLAlchemy 2.x declarative models.
    """
    pass


class UUIDMixin:
    """
    Mixin providing a UUID primary key.
    """
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )


class CreatedAtMixin:
    """
    Mixin providing created_at timezone-aware timestamp.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class UpdatedAtMixin:
    """
    Mixin providing updated_at timezone-aware timestamp with auto-update.
    """
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class TimestampMixin(CreatedAtMixin, UpdatedAtMixin):
    """
    Combined mixin providing both created_at and updated_at timestamps.
    """
    pass
