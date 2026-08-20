import uuid
from typing import Dict
import pytest
from httpx import AsyncClient
from app.models.campaign import EmailCampaign
from app.models.contact_list import ContactList
from app.models.template import EmailTemplate
from app.models.user import User


@pytest.mark.asyncio
async def test_create_campaign_success(
    async_client: AsyncClient,
    user_a: User,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """Test creating an email campaign defaults to DRAFT status."""
    payload = {
        "name": "Summer Product Launch",
        "subject": "Introducing our summer lineup",
        "template_id": str(template_a.id),
        "contact_list_id": str(contact_list_a.id),
    }
    response = await async_client.post("/api/v1/campaigns", json=payload, headers=auth_headers_a)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["subject"] == payload["subject"]
    assert data["template_id"] == str(template_a.id)
    assert data["contact_list_id"] == str(contact_list_a.id)
    assert data["status"] == "draft"
    assert data["owner_id"] == str(user_a.id)
    assert "id" in data


@pytest.mark.asyncio
async def test_create_campaign_validation_errors(
    async_client: AsyncClient,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """Test validation errors for empty name/subject."""
    resp1 = await async_client.post(
        "/api/v1/campaigns",
        json={"name": "", "subject": "Sub", "template_id": str(template_a.id), "contact_list_id": str(contact_list_a.id)},
        headers=auth_headers_a,
    )
    assert resp1.status_code == 422

    resp2 = await async_client.post(
        "/api/v1/campaigns",
        json={"name": "Name", "subject": "", "template_id": str(template_a.id), "contact_list_id": str(contact_list_a.id)},
        headers=auth_headers_a,
    )
    assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_create_campaign_foreign_template_rejected(
    async_client: AsyncClient,
    template_b: EmailTemplate,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """
    CRITICAL: User A attempts to create a campaign using User B's template.
    Must return 404 Not Found.
    """
    payload = {
        "name": "Malicious Campaign",
        "subject": "Subject",
        "template_id": str(template_b.id),
        "contact_list_id": str(contact_list_a.id),
    }
    response = await async_client.post("/api/v1/campaigns", json=payload, headers=auth_headers_a)
    assert response.status_code == 404
    assert "template" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_campaign_foreign_contact_list_rejected(
    async_client: AsyncClient,
    template_a: EmailTemplate,
    contact_list_b: ContactList,
    auth_headers_a: Dict[str, str],
):
    """
    CRITICAL: User A attempts to create a campaign using User B's contact list.
    Must return 404 Not Found.
    """
    payload = {
        "name": "Malicious Campaign",
        "subject": "Subject",
        "template_id": str(template_a.id),
        "contact_list_id": str(contact_list_b.id),
    }
    response = await async_client.post("/api/v1/campaigns", json=payload, headers=auth_headers_a)
    assert response.status_code == 404
    assert "contact list" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_campaigns_pagination_and_filters(
    async_client: AsyncClient,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """Test pagination, search, and status filtering for campaigns."""
    for i in range(12):
        await async_client.post(
            "/api/v1/campaigns",
            json={
                "name": f"Campaign Alpha {i:02d}",
                "subject": f"Subject {i}",
                "template_id": str(template_a.id),
                "contact_list_id": str(contact_list_a.id),
            },
            headers=auth_headers_a,
        )

    # 1. Pagination
    resp_p1 = await async_client.get("/api/v1/campaigns?page=1&page_size=10", headers=auth_headers_a)
    assert resp_p1.status_code == 200
    data_p1 = resp_p1.json()
    assert len(data_p1["items"]) == 10
    assert data_p1["total"] == 12
    assert data_p1["total_pages"] == 2

    # 2. Search
    resp_search = await async_client.get("/api/v1/campaigns?search=Alpha 05", headers=auth_headers_a)
    assert resp_search.status_code == 200
    assert resp_search.json()["total"] == 1

    # 3. Status filter
    resp_draft = await async_client.get("/api/v1/campaigns?status=draft", headers=auth_headers_a)
    assert resp_draft.status_code == 200
    assert resp_draft.json()["total"] == 12


@pytest.mark.asyncio
async def test_get_campaign_by_id(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
    auth_headers_a: Dict[str, str],
):
    """Test getting single campaign by ID."""
    response = await async_client.get(f"/api/v1/campaigns/{campaign_a.id}", headers=auth_headers_a)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(campaign_a.id)
    assert data["name"] == campaign_a.name
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_update_draft_campaign(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
    auth_headers_a: Dict[str, str],
):
    """Test updating a campaign in DRAFT status."""
    payload = {
        "name": "Revised Campaign Name",
        "subject": "Revised Subject Line",
    }
    response = await async_client.patch(
        f"/api/v1/campaigns/{campaign_a.id}",
        json=payload,
        headers=auth_headers_a,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Revised Campaign Name"
    assert data["subject"] == "Revised Subject Line"


@pytest.mark.asyncio
async def test_update_ready_campaign_rejected(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
    auth_headers_a: Dict[str, str],
):
    """
    CRITICAL: READY campaigns are immutable.
    Attempting to PATCH a READY campaign must return 400 Bad Request.
    """
    # 1. Transition to READY
    ready_resp = await async_client.post(f"/api/v1/campaigns/{campaign_a.id}/ready", headers=auth_headers_a)
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "ready"

    # 2. Attempt to PATCH
    patch_resp = await async_client.patch(
        f"/api/v1/campaigns/{campaign_a.id}",
        json={"name": "Attempted Edit on Ready"},
        headers=auth_headers_a,
    )
    assert patch_resp.status_code == 400
    assert "cannot edit campaign in 'ready'" in patch_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_campaign(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
    auth_headers_a: Dict[str, str],
):
    """Test deleting campaign returns 204 No Content."""
    del_resp = await async_client.delete(f"/api/v1/campaigns/{campaign_a.id}", headers=auth_headers_a)
    assert del_resp.status_code == 204

    get_resp = await async_client.get(f"/api/v1/campaigns/{campaign_a.id}", headers=auth_headers_a)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_cross_user_campaign_isolation(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
    auth_headers_b: Dict[str, str],
):
    """
    CRITICAL: User B attempts to access User A's campaign.
    Must return 404 Not Found.
    """
    # GET
    resp_get = await async_client.get(f"/api/v1/campaigns/{campaign_a.id}", headers=auth_headers_b)
    assert resp_get.status_code == 404

    # PATCH
    resp_patch = await async_client.patch(
        f"/api/v1/campaigns/{campaign_a.id}",
        json={"name": "Hacked"},
        headers=auth_headers_b,
    )
    assert resp_patch.status_code == 404

    # DELETE
    resp_delete = await async_client.delete(f"/api/v1/campaigns/{campaign_a.id}", headers=auth_headers_b)
    assert resp_delete.status_code == 404
