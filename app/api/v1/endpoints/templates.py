from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.template import TemplateCreate, TemplateResponse, TemplateUpdate
from app.services.template_service import template_service

router = APIRouter()


@router.post(
    "",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an email template",
)
async def create_template(
    template_in: TemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new email template owned by the authenticated user.
    """
    return await template_service.create(db, owner_id=current_user.id, template_in=template_in)


@router.get(
    "",
    response_model=PaginatedResponse[TemplateResponse],
    status_code=status.HTTP_200_OK,
    summary="List email templates for current user",
)
async def list_templates(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    search: Optional[str] = Query(default=None, description="Search template name or subject"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve paginated email templates owned by the authenticated user.
    """
    return await template_service.list_by_owner(
        db,
        owner_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
    )


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get email template by ID",
)
async def get_template(
    template_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a specific email template owned by the authenticated user.
    """
    return await template_service.get_by_id(db, template_id=template_id, owner_id=current_user.id)


@router.patch(
    "/{template_id}",
    response_model=TemplateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update email template by ID",
)
async def update_template(
    template_id: UUID,
    template_in: TemplateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update details of an email template owned by the authenticated user.
    """
    return await template_service.update(
        db,
        template_id=template_id,
        owner_id=current_user.id,
        template_in=template_in,
    )


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete email template by ID",
)
async def delete_template(
    template_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an email template owned by the authenticated user.
    Fails with 409 Conflict if the template is referenced by active campaigns.
    """
    await template_service.delete(db, template_id=template_id, owner_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
