"""v2_campaign_engine

Revision ID: 002_v2_campaign_engine
Revises: 001_initial_v1
Create Date: 2026-08-20 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_v2_campaign_engine"
down_revision: Union[str, None] = "001_initial_v1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create email_templates table
    op.create_table(
        "email_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("html_content", sa.Text(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_templates_id"), "email_templates", ["id"], unique=False)
    op.create_index(op.f("ix_email_templates_owner_id"), "email_templates", ["owner_id"], unique=False)

    # 2. Create email_campaigns table
    op.create_table(
        "email_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_list_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["contact_list_id"], ["contact_lists.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["email_templates.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_campaigns_id"), "email_campaigns", ["id"], unique=False)
    op.create_index(op.f("ix_email_campaigns_owner_id"), "email_campaigns", ["owner_id"], unique=False)
    op.create_index(op.f("ix_email_campaigns_template_id"), "email_campaigns", ["template_id"], unique=False)
    op.create_index(op.f("ix_email_campaigns_contact_list_id"), "email_campaigns", ["contact_list_id"], unique=False)
    op.create_index(op.f("ix_email_campaigns_status"), "email_campaigns", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_email_campaigns_status"), table_name="email_campaigns")
    op.drop_index(op.f("ix_email_campaigns_contact_list_id"), table_name="email_campaigns")
    op.drop_index(op.f("ix_email_campaigns_template_id"), table_name="email_campaigns")
    op.drop_index(op.f("ix_email_campaigns_owner_id"), table_name="email_campaigns")
    op.drop_index(op.f("ix_email_campaigns_id"), table_name="email_campaigns")
    op.drop_table("email_campaigns")

    op.drop_index(op.f("ix_email_templates_owner_id"), table_name="email_templates")
    op.drop_index(op.f("ix_email_templates_id"), table_name="email_templates")
    op.drop_table("email_templates")
