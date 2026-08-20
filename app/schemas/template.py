from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    subject: str = Field(..., min_length=1, max_length=255, description="Email subject line")
    html_content: str = Field(..., min_length=1, description="HTML body content")
    text_content: Optional[str] = Field(default=None, description="Optional plain-text body content")


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Updated template name")
    subject: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Updated email subject line")
    html_content: Optional[str] = Field(default=None, min_length=1, description="Updated HTML body content")
    text_content: Optional[str] = Field(default=None, description="Updated plain-text body content")


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    created_at: datetime
    updated_at: datetime
