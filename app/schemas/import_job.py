from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ImportStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportJobCreateResponse(BaseModel):
    import_id: UUID
    status: str
    message: str


class ImportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    contact_list_id: UUID
    status: str
    original_filename: str
    total_rows: int
    processed_rows: int
    imported_rows: int
    skipped_rows: int
    duplicate_rows: int
    invalid_rows: int
    error_count: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ImportErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    import_job_id: UUID
    row_number: int
    error_type: str
    message: str
    created_at: datetime
