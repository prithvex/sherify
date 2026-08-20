from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class RecipientStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    # Reserved future states
    OPENED = "opened"
    CLICKED = "clicked"


class CampaignRecipientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    campaign_id: UUID
    subscriber_id: Optional[UUID] = None
    email: str
    tracking_token: str
    status: str
    attempts: int
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
