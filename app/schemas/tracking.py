from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TrackingEventType(str, Enum):
    OPENED = "opened"
    BOUNCED = "bounced"


class TrackingEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    campaign_id: UUID
    campaign_recipient_id: UUID
    event_type: str
    occurred_at: datetime
    received_at: datetime
    provider_event_id: Optional[str] = None
    created_at: datetime


class WebhookIngestResponse(BaseModel):
    event_id: UUID
    status: str
    message: str


class WebhookEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str
    provider_event_id: str
    event_type: str
    status: str
    error_message: Optional[str] = None
    received_at: datetime
    processed_at: Optional[datetime] = None
    created_at: datetime


class CampaignStatsResponse(BaseModel):
    campaign_id: UUID
    total_recipients: int
    sent_count: int
    failed_count: int
    bounced_count: int
    opened_count: int
    open_rate: float
    bounce_rate: float
