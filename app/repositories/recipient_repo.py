from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.recipient import CampaignRecipient


class RecipientRepository:
    async def bulk_create(
        self,
        db: AsyncSession,
        recipients: List[CampaignRecipient],
    ) -> None:
        """
        Add a batch of CampaignRecipient instances to session.
        """
        db.add_all(recipients)
        await db.flush()

    async def get_by_tracking_token(
        self,
        db: AsyncSession,
        tracking_token: str,
    ) -> Optional[CampaignRecipient]:
        """
        Find CampaignRecipient by secure tracking token.
        """
        stmt = select(CampaignRecipient).where(CampaignRecipient.tracking_token == tracking_token)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_provider_message_id(
        self,
        db: AsyncSession,
        provider_message_id: str,
    ) -> Optional[CampaignRecipient]:
        """
        Find CampaignRecipient by provider dispatch message ID.
        """
        stmt = select(CampaignRecipient).where(CampaignRecipient.provider_message_id == provider_message_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_unprocessed_batch(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        limit: int = 100,
    ) -> List[CampaignRecipient]:
        """
        Fetch next batch of recipients that are in 'pending' or 'processing' (stale) status.
        """
        stmt = (
            select(CampaignRecipient)
            .where(
                CampaignRecipient.campaign_id == campaign_id,
                CampaignRecipient.status.in_(["pending", "processing"]),
            )
            .order_by(CampaignRecipient.created_at.asc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_unprocessed(
        self,
        db: AsyncSession,
        campaign_id: UUID,
    ) -> int:
        """
        Count recipients remaining in 'pending' or 'processing' status.
        """
        stmt = (
            select(func.count(CampaignRecipient.id))
            .where(
                CampaignRecipient.campaign_id == campaign_id,
                CampaignRecipient.status.in_(["pending", "processing"]),
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    async def get_status_counts(
        self,
        db: AsyncSession,
        campaign_id: UUID,
    ) -> Dict[str, int]:
        """
        Get total counts grouped by recipient status.
        """
        stmt = (
            select(CampaignRecipient.status, func.count(CampaignRecipient.id))
            .where(CampaignRecipient.campaign_id == campaign_id)
            .group_by(CampaignRecipient.status)
        )
        result = await db.execute(stmt)
        return {status: count for status, count in result.all()}

    async def get_campaign_stats(
        self,
        db: AsyncSession,
        campaign_id: UUID,
    ) -> Dict[str, Any]:
        """
        Calculate database-aggregated delivery and engagement statistics for a campaign.
        """
        stmt = (
            select(
                func.count(CampaignRecipient.id).label("total_recipients"),
                func.count(
                    case(
                        (
                            (CampaignRecipient.status.in_(["sent", "bounced"]))
                            | (CampaignRecipient.sent_at.is_not(None)),
                            1,
                        )
                    )
                ).label("sent_count"),
                func.count(
                    case(
                        (CampaignRecipient.status == "failed", 1)
                    )
                ).label("failed_count"),
                func.count(
                    case(
                        (
                            (CampaignRecipient.status == "bounced")
                            | (CampaignRecipient.bounced_at.is_not(None)),
                            1,
                        )
                    )
                ).label("bounced_count"),
                func.count(
                    case(
                        (CampaignRecipient.opened_at.is_not(None), 1)
                    )
                ).label("opened_count"),
            )
            .where(CampaignRecipient.campaign_id == campaign_id)
        )
        result = await db.execute(stmt)
        row = result.one()

        total = row.total_recipients or 0
        sent = row.sent_count or 0
        failed = row.failed_count or 0
        bounced = row.bounced_count or 0
        opened = row.opened_count or 0

        open_rate = round(opened / sent, 4) if sent > 0 else 0.0
        bounce_rate = round(bounced / sent, 4) if sent > 0 else 0.0

        return {
            "campaign_id": campaign_id,
            "total_recipients": total,
            "sent_count": sent,
            "failed_count": failed,
            "bounced_count": bounced,
            "opened_count": opened,
            "open_rate": open_rate,
            "bounce_rate": bounce_rate,
        }


recipient_repository = RecipientRepository()
