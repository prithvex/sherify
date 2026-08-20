from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import EmailCampaign
from app.repositories.campaign_repo import campaign_repository
from app.repositories.contact_list_repo import contact_list_repository
from app.repositories.template_repo import template_repository
from app.schemas.campaign import CampaignCreate, CampaignResponse, CampaignStatus, CampaignUpdate
from app.schemas.common import PaginatedResponse


class CampaignService:
    async def _validate_foreign_ownership(
        self,
        db: AsyncSession,
        owner_id: UUID,
        template_id: Optional[UUID] = None,
        contact_list_id: Optional[UUID] = None,
    ) -> None:
        """
        Verify that template and contact list exist and belong to the authenticated user.
        """
        if template_id is not None:
            template = await template_repository.get_by_id(db, template_id=template_id, owner_id=owner_id)
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Email template not found",
                )

        if contact_list_id is not None:
            contact_list = await contact_list_repository.get_by_id(db, list_id=contact_list_id, owner_id=owner_id)
            if not contact_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Contact list not found",
                )

    async def create(
        self,
        db: AsyncSession,
        owner_id: UUID,
        campaign_in: CampaignCreate,
    ) -> EmailCampaign:
        await self._validate_foreign_ownership(
            db,
            owner_id=owner_id,
            template_id=campaign_in.template_id,
            contact_list_id=campaign_in.contact_list_id,
        )

        campaign = EmailCampaign(
            owner_id=owner_id,
            name=campaign_in.name.strip(),
            subject=campaign_in.subject.strip(),
            template_id=campaign_in.template_id,
            contact_list_id=campaign_in.contact_list_id,
            status=CampaignStatus.DRAFT.value,
        )
        return await campaign_repository.create(db, campaign)

    async def get_by_id(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        owner_id: UUID,
    ) -> EmailCampaign:
        campaign = await campaign_repository.get_by_id(db, campaign_id=campaign_id, owner_id=owner_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email campaign not found",
            )
        return campaign

    async def list_by_owner(
        self,
        db: AsyncSession,
        owner_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse[CampaignResponse]:
        items, total = await campaign_repository.list_by_owner(
            db,
            owner_id=owner_id,
            page=page,
            page_size=page_size,
            status=status_filter,
            search=search,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        response_items = [CampaignResponse.model_validate(item) for item in items]
        return PaginatedResponse[CampaignResponse](
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        owner_id: UUID,
        campaign_in: CampaignUpdate,
    ) -> EmailCampaign:
        campaign = await self.get_by_id(db, campaign_id=campaign_id, owner_id=owner_id)

        # READY campaigns are immutable
        if campaign.status != CampaignStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot edit campaign in '{campaign.status.upper()}' status. Only DRAFT campaigns can be modified.",
            )

        if campaign_in.template_id is not None or campaign_in.contact_list_id is not None:
            await self._validate_foreign_ownership(
                db,
                owner_id=owner_id,
                template_id=campaign_in.template_id,
                contact_list_id=campaign_in.contact_list_id,
            )

        if campaign_in.name is not None:
            campaign.name = campaign_in.name.strip()
        if campaign_in.subject is not None:
            campaign.subject = campaign_in.subject.strip()
        if campaign_in.template_id is not None:
            campaign.template_id = campaign_in.template_id
        if campaign_in.contact_list_id is not None:
            campaign.contact_list_id = campaign_in.contact_list_id

        return await campaign_repository.update(db, campaign)

    async def delete(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        owner_id: UUID,
    ) -> None:
        campaign = await self.get_by_id(db, campaign_id=campaign_id, owner_id=owner_id)
        await campaign_repository.delete(db, campaign)

    async def transition_ready(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        owner_id: UUID,
    ) -> EmailCampaign:
        """
        Validate and atomically transition a campaign from DRAFT to READY.
        """
        campaign = await self.get_by_id(db, campaign_id=campaign_id, owner_id=owner_id)

        if campaign.status == CampaignStatus.READY.value:
            return campaign

        # 1. Validate campaign name
        if not campaign.name or not campaign.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign must have a valid non-empty name before transitioning to READY",
            )

        # 2. Validate campaign subject
        if not campaign.subject or not campaign.subject.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign must have a valid non-empty subject before transitioning to READY",
            )

        # 3. Validate template exists and belongs to user
        template = await template_repository.get_by_id(db, template_id=campaign.template_id, owner_id=owner_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referenced template does not exist or does not belong to the user",
            )

        # 4. Validate contact list exists and belongs to user
        contact_list = await contact_list_repository.get_by_id(db, list_id=campaign.contact_list_id, owner_id=owner_id)
        if not contact_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referenced contact list does not exist or does not belong to the user",
            )

        # Transition state
        campaign.status = CampaignStatus.READY.value
        return await campaign_repository.update(db, campaign)


campaign_service = CampaignService()
