from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import EmailCampaign


class CampaignRepository:
    async def get_by_id(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        owner_id: Optional[UUID] = None,
    ) -> Optional[EmailCampaign]:
        stmt = select(EmailCampaign).where(EmailCampaign.id == campaign_id)
        if owner_id is not None:
            stmt = stmt.where(EmailCampaign.owner_id == owner_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_owner(
        self,
        db: AsyncSession,
        owner_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[EmailCampaign], int]:
        base_query = select(EmailCampaign).where(EmailCampaign.owner_id == owner_id)
        count_query = select(func.count(EmailCampaign.id)).where(EmailCampaign.owner_id == owner_id)

        if status:
            base_query = base_query.where(EmailCampaign.status == status)
            count_query = count_query.where(EmailCampaign.status == status)

        if search:
            search_pattern = f"%{search.strip()}%"
            filter_expr = (
                EmailCampaign.name.ilike(search_pattern)
                | EmailCampaign.subject.ilike(search_pattern)
            )
            base_query = base_query.where(filter_expr)
            count_query = count_query.where(filter_expr)

        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        offset = (page - 1) * page_size
        stmt = base_query.order_by(EmailCampaign.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def create(self, db: AsyncSession, campaign: EmailCampaign) -> EmailCampaign:
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        return campaign

    async def update(self, db: AsyncSession, campaign: EmailCampaign) -> EmailCampaign:
        await db.commit()
        await db.refresh(campaign)
        return campaign

    async def delete(self, db: AsyncSession, campaign: EmailCampaign) -> None:
        await db.delete(campaign)
        await db.commit()

    async def is_contact_list_referenced(self, db: AsyncSession, contact_list_id: UUID) -> bool:
        stmt = select(func.count(EmailCampaign.id)).where(EmailCampaign.contact_list_id == contact_list_id)
        result = await db.execute(stmt)
        count = result.scalar_one()
        return count > 0


campaign_repository = CampaignRepository()
