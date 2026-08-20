from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.contact_list import ContactListCreate, ContactListResponse, ContactListUpdate
from app.schemas.import_job import ImportJobCreateResponse
from app.schemas.subscriber import SubscriberCreate, SubscriberResponse, SubscriberStatus, SubscriberUpdate
from app.services.contact_list_service import contact_list_service
from app.services.import_service import import_service
from app.services.subscriber_service import subscriber_service

router = APIRouter()


# ============================================================================
# Contact List Endpoints
# ============================================================================

@router.post(
    "",
    response_model=ContactListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new contact list",
)
async def create_contact_list(
    list_in: ContactListCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new contact list owned by the authenticated user.
    """
    return await contact_list_service.create(db, owner_id=current_user.id, list_in=list_in)


@router.get(
    "",
    response_model=PaginatedResponse[ContactListResponse],
    status_code=status.HTTP_200_OK,
    summary="List contact lists for current user",
)
async def list_contact_lists(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    search: Optional[str] = Query(default=None, description="Search contact list name or description"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve paginated contact lists owned by the authenticated user.
    """
    return await contact_list_service.list_by_owner(
        db,
        owner_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
    )


@router.get(
    "/{list_id}",
    response_model=ContactListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get contact list by ID",
)
async def get_contact_list(
    list_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a specific contact list owned by the authenticated user.
    """
    return await contact_list_service.get_by_id(db, list_id=list_id, owner_id=current_user.id)


@router.patch(
    "/{list_id}",
    response_model=ContactListResponse,
    status_code=status.HTTP_200_OK,
    summary="Update contact list by ID",
)
async def update_contact_list(
    list_id: UUID,
    list_in: ContactListUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update details of a contact list owned by the authenticated user.
    """
    return await contact_list_service.update(
        db,
        list_id=list_id,
        owner_id=current_user.id,
        list_in=list_in,
    )


@router.delete(
    "/{list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete contact list by ID",
)
async def delete_contact_list(
    list_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a contact list and all associated subscribers owned by the authenticated user.
    """
    await contact_list_service.delete(db, list_id=list_id, owner_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============================================================================
# Subscriber Endpoints (Nested under Contact Lists)
# ============================================================================

@router.post(
    "/{list_id}/subscribers",
    response_model=SubscriberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add subscriber to contact list",
)
async def create_subscriber(
    list_id: UUID,
    sub_in: SubscriberCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a new subscriber to the specified contact list.
    """
    return await subscriber_service.create(
        db,
        list_id=list_id,
        owner_id=current_user.id,
        sub_in=sub_in,
    )


@router.post(
    "/{list_id}/subscribers/import",
    response_model=ImportJobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Bulk import subscribers via CSV file",
)
async def import_subscribers_csv(
    list_id: UUID,
    file: UploadFile = File(..., description="CSV file containing subscribers"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and queue a CSV file for asynchronous batch subscriber ingestion.
    """
    return await import_service.create_import_job(
        db=db,
        owner_id=current_user.id,
        contact_list_id=list_id,
        file=file,
    )


@router.get(
    "/{list_id}/subscribers",
    response_model=PaginatedResponse[SubscriberResponse],
    status_code=status.HTTP_200_OK,
    summary="List subscribers in contact list",
)
async def list_subscribers(
    list_id: UUID,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    status: Optional[SubscriberStatus] = Query(default=None, description="Filter by subscriber status"),
    search: Optional[str] = Query(default=None, description="Search subscriber email or name"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve paginated subscribers within the specified contact list.
    """
    status_val = status.value if status else None
    return await subscriber_service.list_by_contact_list(
        db,
        list_id=list_id,
        owner_id=current_user.id,
        page=page,
        page_size=page_size,
        status_filter=status_val,
        search=search,
    )


@router.get(
    "/{list_id}/subscribers/{subscriber_id}",
    response_model=SubscriberResponse,
    status_code=status.HTTP_200_OK,
    summary="Get subscriber by ID",
)
async def get_subscriber(
    list_id: UUID,
    subscriber_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a specific subscriber from a contact list.
    """
    return await subscriber_service.get_by_id(
        db,
        list_id=list_id,
        subscriber_id=subscriber_id,
        owner_id=current_user.id,
    )


@router.patch(
    "/{list_id}/subscribers/{subscriber_id}",
    response_model=SubscriberResponse,
    status_code=status.HTTP_200_OK,
    summary="Update subscriber by ID",
)
async def update_subscriber(
    list_id: UUID,
    subscriber_id: UUID,
    sub_in: SubscriberUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a subscriber within a contact list.
    """
    return await subscriber_service.update(
        db,
        list_id=list_id,
        subscriber_id=subscriber_id,
        owner_id=current_user.id,
        sub_in=sub_in,
    )


@router.delete(
    "/{list_id}/subscribers/{subscriber_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete subscriber by ID",
)
async def delete_subscriber(
    list_id: UUID,
    subscriber_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a subscriber from a contact list.
    """
    await subscriber_service.delete(
        db,
        list_id=list_id,
        subscriber_id=subscriber_id,
        owner_id=current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
