from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.import_job import ImportErrorResponse, ImportJobResponse
from app.services.import_service import import_service

router = APIRouter()


@router.get(
    "/{import_job_id}",
    response_model=ImportJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get import job status and summary",
)
async def get_import_job(
    import_job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ImportJobResponse:
    """
    Retrieve status and statistics for a specific subscriber import job.
    """
    return await import_service.get_import_job(
        db=db,
        job_id=import_job_id,
        owner_id=current_user.id,
    )


@router.get(
    "/{import_job_id}/errors",
    response_model=PaginatedResponse[ImportErrorResponse],
    status_code=status.HTTP_200_OK,
    summary="List row validation errors for an import job",
)
async def list_import_errors(
    import_job_id: UUID,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ImportErrorResponse]:
    """
    Retrieve paginated validation/parse errors recorded during CSV import.
    """
    return await import_service.list_import_errors(
        db=db,
        job_id=import_job_id,
        owner_id=current_user.id,
        page=page,
        page_size=page_size,
    )
