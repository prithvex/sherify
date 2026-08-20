from math import ceil
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.import_job import ImportJob
from app.repositories.contact_list_repo import contact_list_repository
from app.repositories.import_error_repo import import_error_repository
from app.repositories.import_job_repo import import_job_repository
from app.schemas.common import PaginatedResponse
from app.schemas.import_job import ImportErrorResponse, ImportJobCreateResponse, ImportJobResponse
from app.storage import get_file_storage
from app.tasks.import_tasks import process_subscriber_import


class ImportService:
    """
    Business logic layer for creating, dispatching, and querying subscriber import jobs.
    """

    async def create_import_job(
        self,
        db: AsyncSession,
        owner_id: UUID,
        contact_list_id: UUID,
        file: UploadFile,
    ) -> ImportJobCreateResponse:
        # 1. Validate ContactList ownership
        contact_list = await contact_list_repository.get_by_id(
            db, list_id=contact_list_id, owner_id=owner_id
        )
        if not contact_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact list not found",
            )

        # 2. Validate File Extension
        filename = file.filename or ""
        if not filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must be a CSV file with .csv extension",
            )

        # 3. Validate File Size
        # Read a small peek / check content length or spool
        file_size = 0
        if file.size is not None:
            file_size = file.size
        max_bytes = settings.MAX_IMPORT_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed limit of {settings.MAX_IMPORT_FILE_SIZE_MB}MB",
            )

        # 4. Save file to storage
        storage = get_file_storage()
        try:
            saved_file_path = await storage.save_file(filename, file)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store uploaded CSV file.",
            )

        # 5. Create ImportJob record
        job = ImportJob(
            owner_id=owner_id,
            contact_list_id=contact_list_id,
            status="queued",
            original_filename=filename,
            file_path=saved_file_path,
        )
        created_job = await import_job_repository.create(db, job)

        # 6. Enqueue Celery task
        try:
            process_subscriber_import.delay(str(created_job.id))
        except Exception as exc:
            # Clean up saved file on queue failure
            storage.delete_file(saved_file_path)
            # Remove job from DB
            await db.delete(created_job)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Background task broker is currently unavailable. Please try again later.",
            )

        return ImportJobCreateResponse(
            import_id=created_job.id,
            status=created_job.status,
            message="Subscriber import queued successfully",
        )

    async def get_import_job(
        self,
        db: AsyncSession,
        job_id: UUID,
        owner_id: UUID,
    ) -> ImportJobResponse:
        job = await import_job_repository.get_by_id(db, job_id=job_id, owner_id=owner_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import job not found",
            )
        return ImportJobResponse.model_validate(job)

    async def list_import_errors(
        self,
        db: AsyncSession,
        job_id: UUID,
        owner_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[ImportErrorResponse]:
        # Validate job existence & ownership
        job = await import_job_repository.get_by_id(db, job_id=job_id, owner_id=owner_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import job not found",
            )

        errors, total = await import_error_repository.list_by_job(
            db, job_id=job_id, page=page, page_size=page_size
        )
        total_pages = ceil(total / page_size) if total > 0 else 1

        return PaginatedResponse[ImportErrorResponse](
            items=[ImportErrorResponse.model_validate(e) for e in errors],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


import_service = ImportService()
