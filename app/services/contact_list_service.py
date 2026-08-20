from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.contact_list import ContactList
from app.repositories.contact_list_repo import contact_list_repository
from app.schemas.common import PaginatedResponse
from app.schemas.contact_list import ContactListCreate, ContactListResponse, ContactListUpdate


class ContactListService:
    async def create(
        self,
        db: AsyncSession,
        owner_id: UUID,
        list_in: ContactListCreate,
    ) -> ContactList:
        contact_list = ContactList(
            owner_id=owner_id,
            name=list_in.name.strip(),
            description=list_in.description.strip() if list_in.description else None,
        )
        return await contact_list_repository.create(db, contact_list)

    async def get_by_id(
        self,
        db: AsyncSession,
        list_id: UUID,
        owner_id: UUID,
    ) -> ContactList:
        contact_list = await contact_list_repository.get_by_id(db, list_id=list_id, owner_id=owner_id)
        if not contact_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact list not found",
            )
        return contact_list

    async def list_by_owner(
        self,
        db: AsyncSession,
        owner_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> PaginatedResponse[ContactListResponse]:
        items, total = await contact_list_repository.list_by_owner(
            db,
            owner_id=owner_id,
            page=page,
            page_size=page_size,
            search=search,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        response_items = [ContactListResponse.model_validate(item) for item in items]
        return PaginatedResponse[ContactListResponse](
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update(
        self,
        db: AsyncSession,
        list_id: UUID,
        owner_id: UUID,
        list_in: ContactListUpdate,
    ) -> ContactList:
        contact_list = await self.get_by_id(db, list_id=list_id, owner_id=owner_id)
        if list_in.name is not None:
            contact_list.name = list_in.name.strip()
        if list_in.description is not None:
            contact_list.description = list_in.description.strip() if list_in.description else None

        return await contact_list_repository.update(db, contact_list)

    async def delete(
        self,
        db: AsyncSession,
        list_id: UUID,
        owner_id: UUID,
    ) -> None:
        contact_list = await self.get_by_id(db, list_id=list_id, owner_id=owner_id)
        await contact_list_repository.delete(db, contact_list)


contact_list_service = ContactListService()
