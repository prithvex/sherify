"""v4_bulk_import

Revision ID: 004_v4_bulk_import
Revises: 003_v3_campaign_execution
Create Date: 2026-08-20 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_v4_bulk_import"
down_revision: Union[str, None] = "003_v3_campaign_execution"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create import_jobs table
    op.create_table(
        "import_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_list_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'queued'")),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("processed_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("imported_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("skipped_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("duplicate_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("invalid_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_list_id"], ["contact_lists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_jobs_id"), "import_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_import_jobs_owner_id"), "import_jobs", ["owner_id"], unique=False)
    op.create_index(op.f("ix_import_jobs_contact_list_id"), "import_jobs", ["contact_list_id"], unique=False)
    op.create_index(op.f("ix_import_jobs_status"), "import_jobs", ["status"], unique=False)

    # 2. Create import_errors table
    op.create_table(
        "import_errors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("import_job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("error_type", sa.String(length=100), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["import_job_id"], ["import_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_errors_id"), "import_errors", ["id"], unique=False)
    op.create_index(op.f("ix_import_errors_import_job_id"), "import_errors", ["import_job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_import_errors_import_job_id"), table_name="import_errors")
    op.drop_index(op.f("ix_import_errors_id"), table_name="import_errors")
    op.drop_table("import_errors")

    op.drop_index(op.f("ix_import_jobs_status"), table_name="import_jobs")
    op.drop_index(op.f("ix_import_jobs_contact_list_id"), table_name="import_jobs")
    op.drop_index(op.f("ix_import_jobs_owner_id"), table_name="import_jobs")
    op.drop_index(op.f("ix_import_jobs_id"), table_name="import_jobs")
    op.drop_table("import_jobs")
