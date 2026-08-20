from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import EmailCampaign
from app.models.template import EmailTemplate


class TemplateRepository:
    async def get_by_id(
        self,
        db: AsyncSession,
        template_id: UUID,
        owner_id: Optional[UUID] = None,
    ) -> Optional[EmailTemplate]:
        stmt = select(EmailTemplate).where(EmailTemplate.id == template_id)
        if owner_id is not None:
            stmt = stmt.where(EmailTemplate.owner_id == owner_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_owner(
        self,
        db: AsyncSession,
        owner_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[EmailTemplate], int]:
        base_query = select(EmailTemplate).where(EmailTemplate.owner_id == owner_id)
        count_query = select(func.count(EmailTemplate.id)).where(EmailTemplate.owner_id == owner_id)

        if search:
            search_pattern = f"%{search.strip()}%"
            filter_expr = (
                EmailTemplate.name.ilike(search_pattern)
                | EmailTemplate.subject.ilike(search_pattern)
            )
            base_query = base_query.where(filter_expr)
            count_query = count_query.where(filter_expr)

        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        offset = (page - 1) * page_size
        stmt = base_query.order_by(EmailTemplate.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def create(self, db: AsyncSession, template: EmailTemplate) -> EmailTemplate:
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    async def update(self, db: AsyncSession, template: EmailTemplate) -> EmailTemplate:
        await db.commit()
        await db.refresh(template)
        return template

    async def delete(self, db: AsyncSession, template: EmailTemplate) -> None:
        await db.delete(template)
        await db.commit()

    async def is_referenced_by_campaign(self, db: AsyncSession, template_id: UUID) -> bool:
        stmt = select(func.count(EmailCampaign.id)).where(EmailCampaign.template_id == template_id)
        result = await db.execute(stmt)
        count = result.scalar_one()
        return count > 0


template_repository = TemplateRepository()
