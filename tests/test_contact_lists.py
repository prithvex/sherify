import uuid
from typing import Dict
import pytest
from httpx import AsyncClient
from app.models.contact_list import ContactList
from app.models.user import User


@pytest.mark.asyncio
async def test_create_contact_list_success(
    async_client: AsyncClient,
    user_a: User,
    auth_headers_a: Dict[str, str],
):
    """Test creating a contact list."""
    payload = {
        "name": "Tech Newsletter Subscribers",
        "description": "Weekly tech digest subscribers",
    }
    response = await async_client.post("/api/v1/contact-lists", json=payload, headers=auth_headers_a)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["owner_id"] == str(user_a.id)
    assert "id" in data


@pytest.mark.asyncio
async def test_create_contact_list_validation(
    async_client: AsyncClient,
    auth_headers_a: Dict[str, str],
):
    """Test validation errors when creating a contact list (empty name)."""
    response = await async_client.post("/api/v1/contact-lists", json={"name": ""}, headers=auth_headers_a)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_contact_lists_pagination(
    async_client: AsyncClient,
    auth_headers_a: Dict[str, str],
):
    """Test paginated retrieval of contact lists."""
    for i in range(15):
        await async_client.post(
            "/api/v1/contact-lists",
            json={"name": f"List {i:02d}", "description": f"Description {i}"},
            headers=auth_headers_a,
        )

    # Fetch page 1 with page_size 10
    resp_page_1 = await async_client.get("/api/v1/contact-lists?page=1&page_size=10", headers=auth_headers_a)
    assert resp_page_1.status_code == 200
    data_1 = resp_page_1.json()
    assert len(data_1["items"]) == 10
    assert data_1["total"] == 15
    assert data_1["page"] == 1
    assert data_1["page_size"] == 10
    assert data_1["total_pages"] == 2

    # Fetch page 2
    resp_page_2 = await async_client.get("/api/v1/contact-lists?page=2&page_size=10", headers=auth_headers_a)
    assert resp_page_2.status_code == 200
    data_2 = resp_page_2.json()
    assert len(data_2["items"]) == 5
    assert data_2["page"] == 2


@pytest.mark.asyncio
async def test_list_contact_lists_search(
    async_client: AsyncClient,
    auth_headers_a: Dict[str, str],
):
    """Test searching contact lists by keyword in name or description."""
    await async_client.post("/api/v1/contact-lists", json={"name": "Alpha Product Users"}, headers=auth_headers_a)
    await async_client.post("/api/v1/contact-lists", json={"name": "Beta Testers", "description": "Alpha testers group"}, headers=auth_headers_a)
    await async_client.post("/api/v1/contact-lists", json={"name": "Gamma Audience"}, headers=auth_headers_a)

    resp = await async_client.get("/api/v1/contact-lists?search=alpha", headers=auth_headers_a)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    names = [item["name"] for item in data["items"]]
    assert "Alpha Product Users" in names
    assert "Beta Testers" in names


@pytest.mark.asyncio
async def test_get_contact_list_by_id(
    async_client: AsyncClient,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """Test getting single contact list by ID."""
    response = await async_client.get(f"/api/v1/contact-lists/{contact_list_a.id}", headers=auth_headers_a)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(contact_list_a.id)
    assert data["name"] == contact_list_a.name


@pytest.mark.asyncio
async def test_cross_user_access_contact_list_isolation(
    async_client: AsyncClient,
    contact_list_b: ContactList,
    auth_headers_a: Dict[str, str],
):
    """
    CRITICAL: User A attempts to access/modify User B's contact list.
    Must return 404 Not Found (ownership isolation).
    """
    # User A tries to GET User B's list
    resp_get = await async_client.get(f"/api/v1/contact-lists/{contact_list_b.id}", headers=auth_headers_a)
    assert resp_get.status_code == 404

    # User A tries to PATCH User B's list
    resp_patch = await async_client.patch(
        f"/api/v1/contact-lists/{contact_list_b.id}",
        json={"name": "Hacked Name"},
        headers=auth_headers_a,
    )
    assert resp_patch.status_code == 404

    # User A tries to DELETE User B's list
    resp_delete = await async_client.delete(f"/api/v1/contact-lists/{contact_list_b.id}", headers=auth_headers_a)
    assert resp_delete.status_code == 404


@pytest.mark.asyncio
async def test_contact_list_malicious_id_manipulation(
    async_client: AsyncClient,
    auth_headers_a: Dict[str, str],
):
    """Test querying non-existent / arbitrary random UUIDs."""
    random_id = uuid.uuid4()
    resp = await async_client.get(f"/api/v1/contact-lists/{random_id}", headers=auth_headers_a)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_contact_list(
    async_client: AsyncClient,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """Test updating contact list details."""
    payload = {"name": "Updated List Name", "description": "Updated description"}
    response = await async_client.patch(
        f"/api/v1/contact-lists/{contact_list_a.id}",
        json=payload,
        headers=auth_headers_a,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated List Name"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_contact_list(
    async_client: AsyncClient,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """Test deleting contact list returns 204 No Content and is no longer accessible."""
    resp_delete = await async_client.delete(f"/api/v1/contact-lists/{contact_list_a.id}", headers=auth_headers_a)
    assert resp_delete.status_code == 204

    resp_get = await async_client.get(f"/api/v1/contact-lists/{contact_list_a.id}", headers=auth_headers_a)
    assert resp_get.status_code == 404
