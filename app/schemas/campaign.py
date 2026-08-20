from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    SCHEDULED = "scheduled"
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
    from_name: Optional[str] = Field(default=None, max_length=255, description="Optional custom sender name")
    from_email: Optional[EmailStr] = Field(default=None, description="Optional custom sender email")
    reply_to: Optional[EmailStr] = Field(default=None, description="Optional custom reply-to email")


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Updated campaign name")
    subject: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Updated subject line")
    template_id: Optional[UUID] = Field(default=None, description="Updated EmailTemplate ID")
    contact_list_id: Optional[UUID] = Field(default=None, description="Updated ContactList ID")
    from_name: Optional[str] = Field(default=None, max_length=255, description="Updated sender name")
    from_email: Optional[EmailStr] = Field(default=None, description="Updated sender email")
    reply_to: Optional[EmailStr] = Field(default=None, description="Updated reply-to email")


class CampaignScheduleRequest(BaseModel):
    scheduled_at: datetime = Field(..., description="Target execution timestamp (ISO 8601 UTC)")
    timezone: Optional[str] = Field(default="UTC", max_length=50, description="User's selected timezone identifier (e.g. Asia/Kolkata)")


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    name: str
    subject: str
    template_id: UUID
    contact_list_id: UUID
    status: str
    scheduled_at: Optional[datetime] = None
    timezone: Optional[str] = None
    from_name: Optional[str] = None
    from_email: Optional[str] = None
    reply_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CampaignSendResponse(BaseModel):
    campaign_id: UUID
    status: str
    message: str
