from typing import Dict, List
from unittest.mock import patch
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import EmailCampaign
from app.models.recipient import CampaignRecipient
from app.models.subscriber import Subscriber


@pytest.mark.asyncio
async def test_send_campaign_success(
    async_client: AsyncClient,
    db_session: AsyncSession,
    campaign_a: EmailCampaign,
    subscribers_a: List[Subscriber],
    auth_headers_a: Dict[str, str],
):
    """
    Test sending a READY campaign:
    - Returns HTTP 202 Accepted
    - Status is QUEUED
    - Creates CampaignRecipient records in PENDING status
    """
    # 1. Transition to READY
    ready_resp = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/ready", headers=auth_headers_a)
    assert ready_resp.status_code == 200

    # 2. Queue for send (mock Celery delay to test API queueing)
    with patch("app.tasks.campaign_tasks.execute_campaign_task.delay") as mock_delay:
        response = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/send", headers=auth_headers_a)
        assert response.status_code == 202
        data = response.json()
        assert data["campaign_id"] == str(campaign_a.id)
        assert data["status"] == "queued"
        assert "queued successfully" in data["message"].lower()
        mock_delay.assert_called_once_with(str(campaign_a.id))

    # 3. Verify CampaignRecipient records in DB
    result = await db_session.execute(
        select(CampaignRecipient).where(CampaignRecipient.campaign_id == campaign_a.id)
    )
    recipients = list(result.scalars().all())
    assert len(recipients) == len(subscribers_a)
    for r in recipients:
        assert r.status == "pending"
        assert r.attempts == 0
        assert r.email.startswith("subscriber")


@pytest.mark.asyncio
async def test_send_draft_campaign_rejected(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
    subscribers_a: List[Subscriber],
    auth_headers_a: Dict[str, str],
):
    """Test attempting to send a campaign in DRAFT status is rejected (400 Bad Request)."""
    assert campaign_a.status == "draft"

    resp = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/send", headers=auth_headers_a)
    assert resp.status_code == 400
    assert "ready" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_send_empty_contact_list_rejected(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
    auth_headers_a: Dict[str, str],
):
    """Test attempting to send when contact list has no active subscribers is rejected (400 Bad Request)."""
    # Transition to READY
    await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/ready", headers=auth_headers_a)

    resp = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/send", headers=auth_headers_a)
    assert resp.status_code == 400
    assert "no active subscribers" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_duplicate_send_request_rejected(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
    subscribers_a: List[Subscriber],
    auth_headers_a: Dict[str, str],
):
    """
    Test duplicate send requests on an already QUEUED campaign are rejected.
    """
    await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/ready", headers=auth_headers_a)

    with patch("app.tasks.campaign_tasks.execute_campaign_task.delay"):
        # First send -> QUEUED (202)
        resp1 = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/send", headers=auth_headers_a)
        assert resp1.status_code == 202

        # Second send immediately -> 400 Bad Request
        resp2 = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/send", headers=auth_headers_a)
        assert resp2.status_code == 400
        assert "cannot be sent in 'queued'" in resp2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cross_user_send_rejected(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
    subscribers_a: List[Subscriber],
    auth_headers_b: Dict[str, str],
):
    """Test User B cannot send User A's campaign (404 Not Found)."""
    resp = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/send", headers=auth_headers_b)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_send_redis_failure_handled(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
    subscribers_a: List[Subscriber],
    auth_headers_a: Dict[str, str],
):
    """
    Test that if the message broker is unavailable, the endpoint returns 503
    and resets the campaign status back to READY.
    """
    await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/ready", headers=auth_headers_a)

    with patch("app.tasks.campaign_tasks.execute_campaign_task.delay", side_effect=Exception("Redis connection refused")):
        resp = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/send", headers=auth_headers_a)
        assert resp.status_code == 503
        assert "broker is temporarily unavailable" in resp.json()["detail"].lower()

    # Verify campaign remained READY so user can retry
    get_resp = await async_client.get(f"/api/v1/campaigns/{campaign_a.id}", headers=auth_headers_a)
    assert get_resp.json()["status"] == "ready"
