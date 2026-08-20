"""v5_tracking_and_webhooks

Revision ID: 005_v5_tracking_and_webhooks
Revises: 004_v4_bulk_import
Create Date: 2026-08-20 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_v5_tracking_and_webhooks"
down_revision: Union[str, None] = "004_v4_bulk_import"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extend campaign_recipients table with tracking columns
    op.add_column(
        "campaign_recipients",
        sa.Column(
            "tracking_token",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("md5(random()::text || clock_timestamp()::text)"),
        ),
    )
    op.add_column(
        "campaign_recipients",
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "campaign_recipients",
        sa.Column("bounced_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_campaign_recipients_tracking_token"),
        "campaign_recipients",
        ["tracking_token"],
        unique=True,
    )
    op.create_index(
        op.f("ix_campaign_recipients_provider_message_id"),
        "campaign_recipients",
        ["provider_message_id"],
        unique=False,
    )

    # 2. Create tracking_events table
    op.create_table(
        "tracking_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_recipient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["email_campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_recipient_id"], ["campaign_recipients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tracking_events_id"), "tracking_events", ["id"], unique=False)
    op.create_index(op.f("ix_tracking_events_campaign_id"), "tracking_events", ["campaign_id"], unique=False)
    op.create_index(op.f("ix_tracking_events_campaign_recipient_id"), "tracking_events", ["campaign_recipient_id"], unique=False)
    op.create_index(op.f("ix_tracking_events_event_type"), "tracking_events", ["event_type"], unique=False)

    # 3. Create webhook_events table
    op.create_table(
        "webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("payload_json", sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False),
        sa.Column("status", sa.String(length=50), server_default=sa.text("'received'"), nullable=False),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_event_id", name="uq_webhook_provider_event"),
    )
    op.create_index(op.f("ix_webhook_events_id"), "webhook_events", ["id"], unique=False)
    op.create_index(op.f("ix_webhook_events_status"), "webhook_events", ["status"], unique=False)


def downgrade() -> None:
    # 1. Drop webhook_events
    op.drop_index(op.f("ix_webhook_events_status"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_id"), table_name="webhook_events")
    op.drop_table("webhook_events")

    # 2. Drop tracking_events
    op.drop_index(op.f("ix_tracking_events_event_type"), table_name="tracking_events")
    op.drop_index(op.f("ix_tracking_events_campaign_recipient_id"), table_name="tracking_events")
    op.drop_index(op.f("ix_tracking_events_campaign_id"), table_name="tracking_events")
    op.drop_index(op.f("ix_tracking_events_id"), table_name="tracking_events")
    op.drop_table("tracking_events")

    # 3. Revert campaign_recipients columns
    op.drop_index(op.f("ix_campaign_recipients_provider_message_id"), table_name="campaign_recipients")
    op.drop_index(op.f("ix_campaign_recipients_tracking_token"), table_name="campaign_recipients")
    op.drop_column("campaign_recipients", "bounced_at")
    op.drop_column("campaign_recipients", "opened_at")
    op.drop_column("campaign_recipients", "tracking_token")
