from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.template import EmailTemplate
from app.repositories.template_repo import template_repository
from app.schemas.common import PaginatedResponse
from app.schemas.template import TemplateCreate, TemplateResponse, TemplateUpdate


class TemplateService:
    async def create(
        self,
        db: AsyncSession,
        owner_id: UUID,
        template_in: TemplateCreate,
    ) -> EmailTemplate:
        template = EmailTemplate(
            owner_id=owner_id,
            name=template_in.name.strip(),
            subject=template_in.subject.strip(),
            html_content=template_in.html_content.strip(),
            text_content=template_in.text_content.strip() if template_in.text_content else None,
        )
        return await template_repository.create(db, template)

    async def get_by_id(
        self,
        db: AsyncSession,
        template_id: UUID,
        owner_id: UUID,
    ) -> EmailTemplate:
        template = await template_repository.get_by_id(db, template_id=template_id, owner_id=owner_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email template not found",
            )
        return template

    async def list_by_owner(
        self,
        db: AsyncSession,
        owner_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> PaginatedResponse[TemplateResponse]:
        items, total = await template_repository.list_by_owner(
            db,
            owner_id=owner_id,
            page=page,
            page_size=page_size,
            search=search,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        response_items = [TemplateResponse.model_validate(item) for item in items]
        return PaginatedResponse[TemplateResponse](
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update(
        self,
        db: AsyncSession,
        template_id: UUID,
        owner_id: UUID,
        template_in: TemplateUpdate,
    ) -> EmailTemplate:
        template = await self.get_by_id(db, template_id=template_id, owner_id=owner_id)

        if template_in.name is not None:
            template.name = template_in.name.strip()
        if template_in.subject is not None:
            template.subject = template_in.subject.strip()
        if template_in.html_content is not None:
            template.html_content = template_in.html_content.strip()
        if template_in.text_content is not None:
            template.text_content = template_in.text_content.strip() if template_in.text_content else None

        return await template_repository.update(db, template)

    async def delete(
        self,
        db: AsyncSession,
        template_id: UUID,
        owner_id: UUID,
    ) -> None:
        template = await self.get_by_id(db, template_id=template_id, owner_id=owner_id)

        is_referenced = await template_repository.is_referenced_by_campaign(db, template_id=template_id)
        if is_referenced:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Template cannot be deleted because it is referenced by existing campaigns",
            )

        await template_repository.delete(db, template)


template_service = TemplateService()
