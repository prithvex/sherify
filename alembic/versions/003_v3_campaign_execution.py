"""v3_campaign_execution

Revision ID: 003_v3_campaign_execution
Revises: 002_v2_campaign_engine
Create Date: 2026-08-20 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_v3_campaign_execution"
down_revision: Union[str, None] = "002_v2_campaign_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create campaign_recipients table
    op.create_table(
        "campaign_recipients",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscriber_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["email_campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscriber_id"], ["subscribers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "email", name="uq_campaign_recipient_email"),
    )
    op.create_index(op.f("ix_campaign_recipients_id"), "campaign_recipients", ["id"], unique=False)
    op.create_index(op.f("ix_campaign_recipients_campaign_id"), "campaign_recipients", ["campaign_id"], unique=False)
    op.create_index(op.f("ix_campaign_recipients_subscriber_id"), "campaign_recipients", ["subscriber_id"], unique=False)
    op.create_index(op.f("ix_campaign_recipients_status"), "campaign_recipients", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_campaign_recipients_status"), table_name="campaign_recipients")
    op.drop_index(op.f("ix_campaign_recipients_subscriber_id"), table_name="campaign_recipients")
    op.drop_index(op.f("ix_campaign_recipients_campaign_id"), table_name="campaign_recipients")
    op.drop_index(op.f("ix_campaign_recipients_id"), table_name="campaign_recipients")
    op.drop_table("campaign_recipients")
