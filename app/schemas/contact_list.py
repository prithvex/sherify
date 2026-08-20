from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ContactListCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the contact list")
    description: Optional[str] = Field(default=None, max_length=1000, description="Optional description")


class ContactListUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Updated name")
    description: Optional[str] = Field(default=None, max_length=1000, description="Updated description")


class ContactListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    name: str
    description: Optional[str] = None
    subscriber_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime
