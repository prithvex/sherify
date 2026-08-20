from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.campaign import (
    CampaignCreate,
    CampaignResponse,
    CampaignScheduleRequest,
    CampaignSendResponse,
    CampaignStatus,
    CampaignUpdate,
)
from app.schemas.common import PaginatedResponse
from app.schemas.tracking import CampaignStatsResponse
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


@router.get(
    "/{campaign_id}/stats",
    response_model=CampaignStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get delivery and engagement statistics for a campaign",
)
async def get_campaign_stats(
    campaign_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CampaignStatsResponse:
    """
    Retrieve database-aggregated delivery and engagement stats (sent, failed, bounced, opened, rates).
    """
    return await campaign_service.get_campaign_stats(
        db=db,
        campaign_id=campaign_id,
        owner_id=current_user.id,
    )


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
    Modifications are rejected if the campaign is already in READY or later status.
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


@router.post(
    "/{campaign_id}/send",
    response_model=CampaignSendResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue campaign for background asynchronous execution",
)
async def send_campaign(
    campaign_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate READY status, create recipient execution snapshots, set status to QUEUED,
    and enqueue Celery background worker execution. Returns HTTP 202 Accepted immediately.
    """
    campaign = await campaign_service.queue_campaign(
        db,
        campaign_id=campaign_id,
        owner_id=current_user.id,
    )
    return CampaignSendResponse(
        campaign_id=campaign.id,
        status=campaign.status,
        message="Campaign queued successfully",
    )


@router.post(
    "/{campaign_id}/schedule",
    response_model=CampaignResponse,
    status_code=status.HTTP_200_OK,
    summary="Schedule a READY campaign for future asynchronous dispatch",
)
async def schedule_campaign(
    campaign_id: UUID,
    schedule_in: CampaignScheduleRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Schedule a campaign in READY status to be dispatched at a specified future UTC time.
    """
    return await campaign_service.schedule_campaign(
        db,
        campaign_id=campaign_id,
        owner_id=current_user.id,
        schedule_in=schedule_in,
    )


@router.post(
    "/{campaign_id}/cancel",
    response_model=CampaignResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel a scheduled, queued, or ready campaign",
)
async def cancel_campaign(
    campaign_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel an uncompleted campaign (SCHEDULED, QUEUED, or READY).
    """
    return await campaign_service.cancel_campaign(
        db,
        campaign_id=campaign_id,
        owner_id=current_user.id,
    )
