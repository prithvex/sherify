from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subscriber import Subscriber


class SubscriberRepository:
    async def get_by_id(
        self,
        db: AsyncSession,
        subscriber_id: UUID,
        contact_list_id: Optional[UUID] = None,
    ) -> Optional[Subscriber]:
        stmt = select(Subscriber).where(Subscriber.id == subscriber_id)
        if contact_list_id is not None:
            stmt = stmt.where(Subscriber.contact_list_id == contact_list_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        db: AsyncSession,
        contact_list_id: UUID,
        email: str,
    ) -> Optional[Subscriber]:
        stmt = select(Subscriber).where(
            Subscriber.contact_list_id == contact_list_id,
            Subscriber.email == email.strip().lower(),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_contact_list(
        self,
        db: AsyncSession,
        contact_list_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Subscriber], int]:
        base_query = select(Subscriber).where(Subscriber.contact_list_id == contact_list_id)
        count_query = select(func.count(Subscriber.id)).where(Subscriber.contact_list_id == contact_list_id)

        if status:
            base_query = base_query.where(Subscriber.status == status)
            count_query = count_query.where(Subscriber.status == status)

        if search:
            search_pattern = f"%{search.strip()}%"
            filter_expr = (
                Subscriber.email.ilike(search_pattern)
                | Subscriber.first_name.ilike(search_pattern)
                | Subscriber.last_name.ilike(search_pattern)
            )
            base_query = base_query.where(filter_expr)
            count_query = count_query.where(filter_expr)

        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        offset = (page - 1) * page_size
        stmt = base_query.order_by(Subscriber.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def create(self, db: AsyncSession, subscriber: Subscriber) -> Subscriber:
        db.add(subscriber)
        await db.commit()
        await db.refresh(subscriber)
        return subscriber

    async def update(self, db: AsyncSession, subscriber: Subscriber) -> Subscriber:
        await db.commit()
        await db.refresh(subscriber)
        return subscriber

    async def delete(self, db: AsyncSession, subscriber: Subscriber) -> None:
        await db.delete(subscriber)
        await db.commit()


subscriber_repository = SubscriberRepository()
