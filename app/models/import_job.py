import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, CreatedAtMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.contact_list import ContactList
    from app.models.user import User


class ImportJob(Base, UUIDMixin, TimestampMixin):
    """
    ImportJob tracks the asynchronous processing, metrics, and state of a bulk subscriber CSV upload.
    """
    __tablename__ = "import_jobs"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contact_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="queued",
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    total_rows: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    processed_rows: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    imported_rows: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    skipped_rows: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    duplicate_rows: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    invalid_rows: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    error_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
    )
    contact_list: Mapped["ContactList"] = relationship(
        "ContactList",
    )
    errors: Mapped[List["ImportError"]] = relationship(
        "ImportError",
        back_populates="import_job",
        cascade="all, delete-orphan",
    )


class ImportError(Base, UUIDMixin, CreatedAtMixin):
    """
    ImportError records structured validation or parsing errors encountered for specific CSV rows.
    """
    __tablename__ = "import_errors"

    import_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    error_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Relationships
    import_job: Mapped["ImportJob"] = relationship(
        "ImportJob",
        back_populates="errors",
    )
