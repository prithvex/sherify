from typing import Dict
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import EmailCampaign
from app.models.contact_list import ContactList
from app.models.template import EmailTemplate


@pytest.mark.asyncio
async def test_transition_ready_success(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
    auth_headers_a: Dict[str, str],
):
    """Test valid campaign successfully transitions from DRAFT to READY."""
    assert campaign_a.status == "draft"

    response = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/ready", headers=auth_headers_a)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["id"] == str(campaign_a.id)

    # Verify persisted status
    get_resp = await async_client.get(f"/api/v1/campaigns/{campaign_a.id}", headers=auth_headers_a)
    assert get_resp.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_transition_ready_idempotent(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
    auth_headers_a: Dict[str, str],
):
    """Test calling /ready on an already READY campaign is safe and idempotent."""
    resp1 = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/ready", headers=auth_headers_a)
    assert resp1.status_code == 200

    resp2 = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/ready", headers=auth_headers_a)
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_transition_ready_foreign_template_fails(
    async_client: AsyncClient,
    db_session: AsyncSession,
    campaign_a: EmailCampaign,
    template_b: EmailTemplate,
    auth_headers_a: Dict[str, str],
):
    """
    Test transition to READY fails and remains DRAFT if template belongs to another user.
    """
    # Force template_id to template_b (User B's template) in DB
    await db_session.execute(
        update(EmailCampaign)
        .where(EmailCampaign.id == campaign_a.id)
        .values(template_id=template_b.id)
    )
    await db_session.commit()

    resp = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/ready", headers=auth_headers_a)
    assert resp.status_code == 400
    assert "template" in resp.json()["detail"].lower()

    # Verify campaign remains DRAFT
    get_resp = await async_client.get(f"/api/v1/campaigns/{campaign_a.id}", headers=auth_headers_a)
    assert get_resp.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_transition_ready_foreign_contact_list_fails(
    async_client: AsyncClient,
    db_session: AsyncSession,
    campaign_a: EmailCampaign,
    contact_list_b: ContactList,
    auth_headers_a: Dict[str, str],
):
    """
    Test transition to READY fails and remains DRAFT if contact list belongs to another user.
    """
    # Force contact_list_id to contact_list_b (User B's list) in DB
    await db_session.execute(
        update(EmailCampaign)
        .where(EmailCampaign.id == campaign_a.id)
        .values(contact_list_id=contact_list_b.id)
    )
    await db_session.commit()

    resp = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/ready", headers=auth_headers_a)
    assert resp.status_code == 400
    assert "contact list" in resp.json()["detail"].lower()

    # Verify campaign remains DRAFT
    get_resp = await async_client.get(f"/api/v1/campaigns/{campaign_a.id}", headers=auth_headers_a)
    assert get_resp.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_transition_ready_cross_user_rejected(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
    auth_headers_b: Dict[str, str],
):
    """Test User B cannot call /ready on User A's campaign (404 Not Found)."""
    resp = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/ready", headers=auth_headers_b)
    assert resp.status_code == 404
