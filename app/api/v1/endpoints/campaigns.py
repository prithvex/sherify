from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.campaign import CampaignCreate, CampaignResponse, CampaignStatus, CampaignUpdate
from app.schemas.common import PaginatedResponse
from app.services.campaign_service import campaign_service

router = APIRouter()


@router.post(
    "",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new email campaign",
)
async def create_campaign(
    campaign_in: CampaignCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new campaign in DRAFT status.
    Verifies that the referenced template and contact list belong to the user.
    """
    return await campaign_service.create(db, owner_id=current_user.id, campaign_in=campaign_in)


@router.get(
    "",
    response_model=PaginatedResponse[CampaignResponse],
    status_code=status.HTTP_200_OK,
    summary="List email campaigns for current user",
)
async def list_campaigns(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    status: Optional[CampaignStatus] = Query(default=None, description="Filter by campaign status"),
    search: Optional[str] = Query(default=None, description="Search campaign name or subject"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve paginated email campaigns owned by the authenticated user.
    """
    status_val = status.value if status else None
    return await campaign_service.list_by_owner(
        db,
        owner_id=current_user.id,
        page=page,
        page_size=page_size,
        status_filter=status_val,
        search=search,
    )


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
    status_code=status.HTTP_200_OK,
    summary="Get email campaign by ID",
)
async def get_campaign(
    campaign_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a specific email campaign owned by the authenticated user.
    """
    return await campaign_service.get_by_id(db, campaign_id=campaign_id, owner_id=current_user.id)


@router.patch(
    "/{campaign_id}",
    response_model=CampaignResponse,
    status_code=status.HTTP_200_OK,
    summary="Update email campaign by ID",
)
async def update_campaign(
    campaign_id: UUID,
    campaign_in: CampaignUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update details of a campaign in DRAFT status.
    Modifications are rejected if the campaign is already in READY status.
    """
    return await campaign_service.update(
        db,
        campaign_id=campaign_id,
        owner_id=current_user.id,
        campaign_in=campaign_in,
    )


@router.delete(
    "/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete email campaign by ID",
)
async def delete_campaign(
    campaign_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an email campaign owned by the authenticated user.
    """
    await campaign_service.delete(db, campaign_id=campaign_id, owner_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{campaign_id}/ready",
    response_model=CampaignResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate and transition campaign to READY status",
)
async def mark_campaign_ready(
    campaign_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate campaign fields, template, and contact list ownership, then transition to READY status.
    """
    return await campaign_service.transition_ready(
        db,
        campaign_id=campaign_id,
        owner_id=current_user.id,
    )
