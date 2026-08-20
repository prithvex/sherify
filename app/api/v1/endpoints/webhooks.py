from typing import Any, Dict
from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.tracking import WebhookIngestResponse
from app.services.webhook_service import webhook_service

router = APIRouter()


@router.post(
    "/email/{provider}",
    response_model=WebhookIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest provider email delivery/bounce webhook",
)
async def receive_email_webhook(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> WebhookIngestResponse:
    """
    Public webhook receiver for email providers (e.g. bounce, open, delivery events).
    Authenticates requests using provider-specific signature verification and enqueues background processing.
    """
    raw_body = await request.body()
    headers = dict(request.headers)
    try:
        payload_json = await request.json()
    except Exception:
        payload_json = {}

    return await webhook_service.ingest_webhook(
        db=db,
        provider=provider,
        raw_body=raw_body,
        headers=headers,
        payload_json=payload_json,
    )
