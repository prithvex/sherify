from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subscriber import Subscriber
from app.repositories.contact_list_repo import contact_list_repository
from app.repositories.subscriber_repo import subscriber_repository
from app.schemas.common import PaginatedResponse
from app.schemas.subscriber import SubscriberCreate, SubscriberResponse, SubscriberUpdate


class SubscriberService:
    async def _verify_list_ownership(self, db: AsyncSession, list_id: UUID, owner_id: UUID):
        contact_list = await contact_list_repository.get_by_id(db, list_id=list_id, owner_id=owner_id)
        if not contact_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact list not found",
            )
        return contact_list

    async def create(
        self,
        db: AsyncSession,
        list_id: UUID,
        owner_id: UUID,
        sub_in: SubscriberCreate,
    ) -> Subscriber:
        await self._verify_list_ownership(db, list_id=list_id, owner_id=owner_id)

        clean_email = sub_in.email.strip().lower()
        existing = await subscriber_repository.get_by_email(db, contact_list_id=list_id, email=clean_email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Subscriber with this email already exists in this contact list",
            )

        subscriber = Subscriber(
            contact_list_id=list_id,
            email=clean_email,
            first_name=sub_in.first_name.strip() if sub_in.first_name else None,
            last_name=sub_in.last_name.strip() if sub_in.last_name else None,
            status=sub_in.status.value,
            metadata_json=sub_in.metadata or {},
        )
        return await subscriber_repository.create(db, subscriber)

    async def get_by_id(
        self,
        db: AsyncSession,
        list_id: UUID,
        subscriber_id: UUID,
        owner_id: UUID,
    ) -> Subscriber:
        await self._verify_list_ownership(db, list_id=list_id, owner_id=owner_id)

        subscriber = await subscriber_repository.get_by_id(
            db,
            subscriber_id=subscriber_id,
            contact_list_id=list_id,
        )
        if not subscriber:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscriber not found in this contact list",
            )
        return subscriber

    async def list_by_contact_list(
        self,
        db: AsyncSession,
        list_id: UUID,
        owner_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse[SubscriberResponse]:
        await self._verify_list_ownership(db, list_id=list_id, owner_id=owner_id)

        items, total = await subscriber_repository.list_by_contact_list(
            db,
            contact_list_id=list_id,
            page=page,
            page_size=page_size,
            status=status_filter,
            search=search,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        response_items = [SubscriberResponse.model_validate(item) for item in items]
        return PaginatedResponse[SubscriberResponse](
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
        subscriber_id: UUID,
        owner_id: UUID,
        sub_in: SubscriberUpdate,
    ) -> Subscriber:
        subscriber = await self.get_by_id(
            db,
            list_id=list_id,
            subscriber_id=subscriber_id,
            owner_id=owner_id,
        )

        if sub_in.email is not None:
            clean_email = sub_in.email.strip().lower()
            if clean_email != subscriber.email:
                existing = await subscriber_repository.get_by_email(
                    db,
                    contact_list_id=list_id,
                    email=clean_email,
                )
                if existing and existing.id != subscriber.id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Subscriber with this email already exists in this contact list",
                    )
                subscriber.email = clean_email

        if sub_in.first_name is not None:
            subscriber.first_name = sub_in.first_name.strip() if sub_in.first_name else None
        if sub_in.last_name is not None:
            subscriber.last_name = sub_in.last_name.strip() if sub_in.last_name else None
        if sub_in.status is not None:
            subscriber.status = sub_in.status.value
        if sub_in.metadata is not None:
            subscriber.metadata_json = sub_in.metadata

        return await subscriber_repository.update(db, subscriber)

    async def delete(
        self,
        db: AsyncSession,
        list_id: UUID,
        subscriber_id: UUID,
        owner_id: UUID,
    ) -> None:
        subscriber = await self.get_by_id(
            db,
            list_id=list_id,
            subscriber_id=subscriber_id,
            owner_id=owner_id,
        )
        await subscriber_repository.delete(db, subscriber)


subscriber_service = SubscriberService()
