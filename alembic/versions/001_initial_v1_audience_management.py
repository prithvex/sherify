"""initial_v1_audience_management

Revision ID: 001_initial_v1
Revises: 
Create Date: 2026-08-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_v1"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. Create contact_lists table
    op.create_table(
        "contact_lists",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contact_lists_id"), "contact_lists", ["id"], unique=False)
    op.create_index(op.f("ix_contact_lists_owner_id"), "contact_lists", ["owner_id"], unique=False)

    # 3. Create subscribers table
    op.create_table(
        "subscribers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_list_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'active'")),
        sa.Column("metadata", sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["contact_list_id"], ["contact_lists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contact_list_id", "email", name="uq_subscriber_contact_list_email"),
    )
    op.create_index(op.f("ix_subscribers_id"), "subscribers", ["id"], unique=False)
    op.create_index(op.f("ix_subscribers_contact_list_id"), "subscribers", ["contact_list_id"], unique=False)
    op.create_index(op.f("ix_subscribers_email"), "subscribers", ["email"], unique=False)
    op.create_index(op.f("ix_subscribers_status"), "subscribers", ["status"], unique=False)
    op.create_index("ix_subscribers_contact_list_status", "subscribers", ["contact_list_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_subscribers_contact_list_status", table_name="subscribers")
    op.drop_index(op.f("ix_subscribers_status"), table_name="subscribers")
    op.drop_index(op.f("ix_subscribers_email"), table_name="subscribers")
    op.drop_index(op.f("ix_subscribers_contact_list_id"), table_name="subscribers")
    op.drop_index(op.f("ix_subscribers_id"), table_name="subscribers")
    op.drop_table("subscribers")

    op.drop_index(op.f("ix_contact_lists_owner_id"), table_name="contact_lists")
    op.drop_index(op.f("ix_contact_lists_id"), table_name="contact_lists")
    op.drop_table("contact_lists")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
