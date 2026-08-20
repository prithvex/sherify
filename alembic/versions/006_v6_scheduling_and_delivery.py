"""v6_scheduling_and_delivery

Revision ID: 006_v6_scheduling_and_delivery
Revises: 005_v5_tracking_and_webhooks
Create Date: 2026-08-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "006_v6_scheduling_and_delivery"
down_revision: Union[str, None] = "005_v5_tracking_and_webhooks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend email_campaigns table with V6 scheduling and sender configuration
    op.add_column(
        "email_campaigns",
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "email_campaigns",
        sa.Column("timezone", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "email_campaigns",
        sa.Column("from_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "email_campaigns",
        sa.Column("from_email", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "email_campaigns",
        sa.Column("reply_to", sa.String(length=255), nullable=True),
    )
    op.create_index(
        op.f("ix_email_campaigns_scheduled_at"),
        "email_campaigns",
        ["scheduled_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_email_campaigns_scheduled_at"), table_name="email_campaigns")
    op.drop_column("email_campaigns", "reply_to")
    op.drop_column("email_campaigns", "from_email")
    op.drop_column("email_campaigns", "from_name")
    op.drop_column("email_campaigns", "timezone")
    op.drop_column("email_campaigns", "scheduled_at")
