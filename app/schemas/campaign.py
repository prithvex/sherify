from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    QUEUED = "queued"
    SENDING = "sending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Campaign name")
    subject: str = Field(..., min_length=1, max_length=255, description="Email subject line")
    template_id: UUID = Field(..., description="Referenced EmailTemplate ID")
    contact_list_id: UUID = Field(..., description="Referenced ContactList ID")


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Updated campaign name")
    subject: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Updated subject line")
    template_id: Optional[UUID] = Field(default=None, description="Updated EmailTemplate ID")
    contact_list_id: Optional[UUID] = Field(default=None, description="Updated ContactList ID")


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    name: str
    subject: str
    template_id: UUID
    contact_list_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


class CampaignSendResponse(BaseModel):
    campaign_id: UUID
    status: str
    message: str
