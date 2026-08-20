import uuid
from typing import Dict
import pytest
from httpx import AsyncClient
from app.models.template import EmailTemplate
from app.models.user import User


@pytest.mark.asyncio
async def test_create_template_success(
    async_client: AsyncClient,
    user_a: User,
    auth_headers_a: Dict[str, str],
):
    """Test creating an email template."""
    payload = {
        "name": "Monthly Newsletter",
        "subject": "Here is what is new this month",
        "html_content": "<p>Hello world newsletter content</p>",
        "text_content": "Hello world newsletter content",
    }
    response = await async_client.post("/api/v1/templates", json=payload, headers=auth_headers_a)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["subject"] == payload["subject"]
    assert data["html_content"] == payload["html_content"]
    assert data["text_content"] == payload["text_content"]
    assert data["owner_id"] == str(user_a.id)
    assert "id" in data


@pytest.mark.asyncio
async def test_create_template_validation_errors(
    async_client: AsyncClient,
    auth_headers_a: Dict[str, str],
):
    """Test validation errors for empty fields."""
    # Empty name
    resp = await async_client.post(
        "/api/v1/templates",
        json={"name": "", "subject": "Subject", "html_content": "<p>Body</p>"},
        headers=auth_headers_a,
    )
    assert resp.status_code == 422

    # Empty subject
    resp = await async_client.post(
        "/api/v1/templates",
        json={"name": "Name", "subject": "", "html_content": "<p>Body</p>"},
        headers=auth_headers_a,
    )
    assert resp.status_code == 422

    # Empty html_content
    resp = await async_client.post(
        "/api/v1/templates",
        json={"name": "Name", "subject": "Subject", "html_content": ""},
        headers=auth_headers_a,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_templates_pagination(
    async_client: AsyncClient,
    auth_headers_a: Dict[str, str],
):
    """Test paginated retrieval of email templates."""
    for i in range(15):
        await async_client.post(
            "/api/v1/templates",
            json={
                "name": f"Template {i:02d}",
                "subject": f"Subject {i}",
                "html_content": f"<p>Content {i}</p>",
            },
            headers=auth_headers_a,
        )

    # Page 1
    resp1 = await async_client.get("/api/v1/templates?page=1&page_size=10", headers=auth_headers_a)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert len(data1["items"]) == 10
    assert data1["total"] == 15
    assert data1["total_pages"] == 2

    # Page 2
    resp2 = await async_client.get("/api/v1/templates?page=2&page_size=10", headers=auth_headers_a)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2["items"]) == 5
    assert data2["page"] == 2


@pytest.mark.asyncio
async def test_list_templates_search(
    async_client: AsyncClient,
    auth_headers_a: Dict[str, str],
):
    """Test search filter on email templates."""
    await async_client.post(
        "/api/v1/templates",
        json={"name": "Weekly Digest", "subject": "Digest for you", "html_content": "<p>Digest</p>"},
        headers=auth_headers_a,
    )
    await async_client.post(
        "/api/v1/templates",
        json={"name": "Flash Sale", "subject": "Weekly Special Sale", "html_content": "<p>Sale</p>"},
        headers=auth_headers_a,
    )
    await async_client.post(
        "/api/v1/templates",
        json={"name": "Onboarding", "subject": "Welcome", "html_content": "<p>Welcome</p>"},
        headers=auth_headers_a,
    )

    resp = await async_client.get("/api/v1/templates?search=weekly", headers=auth_headers_a)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_get_template_by_id(
    async_client: AsyncClient,
    template_a: EmailTemplate,
    auth_headers_a: Dict[str, str],
):
    """Test retrieving a single template by ID."""
    response = await async_client.get(f"/api/v1/templates/{template_a.id}", headers=auth_headers_a)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(template_a.id)
    assert data["name"] == template_a.name


@pytest.mark.asyncio
async def test_update_template(
    async_client: AsyncClient,
    template_a: EmailTemplate,
    auth_headers_a: Dict[str, str],
):
    """Test updating an email template."""
    update_payload = {
        "name": "Updated Template Name",
        "subject": "Updated Subject Line",
        "html_content": "<h2>Updated HTML</h2>",
        "text_content": "Updated text",
    }
    response = await async_client.patch(
        f"/api/v1/templates/{template_a.id}",
        json=update_payload,
        headers=auth_headers_a,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_payload["name"]
    assert data["subject"] == update_payload["subject"]
    assert data["html_content"] == update_payload["html_content"]
    assert data["text_content"] == update_payload["text_content"]


@pytest.mark.asyncio
async def test_delete_template(
    async_client: AsyncClient,
    template_a: EmailTemplate,
    auth_headers_a: Dict[str, str],
):
    """Test deleting an unreferenced email template."""
    del_resp = await async_client.delete(f"/api/v1/templates/{template_a.id}", headers=auth_headers_a)
    assert del_resp.status_code == 204

    get_resp = await async_client.get(f"/api/v1/templates/{template_a.id}", headers=auth_headers_a)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_cross_user_template_isolation(
    async_client: AsyncClient,
    template_b: EmailTemplate,
    auth_headers_a: Dict[str, str],
):
    """
    CRITICAL: User A attempts to read, update or delete User B's template.
    Must return 404 Not Found.
    """
    # GET
    resp_get = await async_client.get(f"/api/v1/templates/{template_b.id}", headers=auth_headers_a)
    assert resp_get.status_code == 404

    # PATCH
    resp_patch = await async_client.patch(
        f"/api/v1/templates/{template_b.id}",
        json={"name": "Hacked Template"},
        headers=auth_headers_a,
    )
    assert resp_patch.status_code == 404

    # DELETE
    resp_delete = await async_client.delete(f"/api/v1/templates/{template_b.id}", headers=auth_headers_a)
    assert resp_delete.status_code == 404


@pytest.mark.asyncio
async def test_template_malicious_id_manipulation(
    async_client: AsyncClient,
    auth_headers_a: Dict[str, str],
):
    """Test querying random non-existent UUIDs."""
    random_id = uuid.uuid4()
    resp = await async_client.get(f"/api/v1/templates/{random_id}", headers=auth_headers_a)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_template_unauthenticated(async_client: AsyncClient):
    """Test template endpoints require authentication."""
    resp = await async_client.get("/api/v1/templates")
    assert resp.status_code == 401
