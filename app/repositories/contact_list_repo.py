from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.contact_list import ContactList


class ContactListRepository:
    async def get_by_id(
        self,
        db: AsyncSession,
        list_id: UUID,
        owner_id: Optional[UUID] = None,
    ) -> Optional[ContactList]:
        stmt = select(ContactList).where(ContactList.id == list_id)
        if owner_id is not None:
            stmt = stmt.where(ContactList.owner_id == owner_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_owner(
        self,
        db: AsyncSession,
        owner_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[ContactList], int]:
        base_query = select(ContactList).where(ContactList.owner_id == owner_id)
        count_query = select(func.count(ContactList.id)).where(ContactList.owner_id == owner_id)

        if search:
            search_pattern = f"%{search.strip()}%"
            filter_expr = ContactList.name.ilike(search_pattern) | ContactList.description.ilike(search_pattern)
            base_query = base_query.where(filter_expr)
            count_query = count_query.where(filter_expr)

        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        offset = (page - 1) * page_size
        stmt = base_query.order_by(ContactList.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def create(self, db: AsyncSession, contact_list: ContactList) -> ContactList:
        db.add(contact_list)
        await db.commit()
        await db.refresh(contact_list)
        return contact_list

    async def update(self, db: AsyncSession, contact_list: ContactList) -> ContactList:
        await db.commit()
        await db.refresh(contact_list)
        return contact_list

    async def delete(self, db: AsyncSession, contact_list: ContactList) -> None:
        await db.delete(contact_list)
        await db.commit()


contact_list_repository = ContactListRepository()
