import uuid
from typing import Dict
import pytest
from httpx import AsyncClient
from app.models.contact_list import ContactList


@pytest.mark.asyncio
async def test_create_subscriber_success(
    async_client: AsyncClient,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """Test adding a subscriber to a contact list."""
    payload = {
        "email": "subscriber1@example.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "status": "active",
        "metadata": {"source": "web_signup", "tier": "gold"},
    }
    response = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        json=payload,
        headers=auth_headers_a,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "subscriber1@example.com"
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["status"] == "active"
    assert data["metadata"] == {"source": "web_signup", "tier": "gold"}
    assert data["contact_list_id"] == str(contact_list_a.id)
    assert "id" in data


@pytest.mark.asyncio
async def test_duplicate_subscriber_in_same_list_rejected(
    async_client: AsyncClient,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """
    Test duplicate email in the SAME contact list returns 409 Conflict.
    """
    payload = {"email": "duplicate@example.com", "first_name": "First"}
    resp1 = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        json=payload,
        headers=auth_headers_a,
    )
    assert resp1.status_code == 201

    resp2 = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        json=payload,
        headers=auth_headers_a,
    )
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_same_subscriber_email_in_different_lists_allowed(
    async_client: AsyncClient,
    contact_list_a: ContactList,
    contact_list_b: ContactList,
    auth_headers_a: Dict[str, str],
    auth_headers_b: Dict[str, str],
):
    """
    Test that subscriber email is NOT globally unique and can exist in multiple contact lists.
    """
    email = "shared_interest@example.com"
    resp_a = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        json={"email": email, "first_name": "User A sub"},
        headers=auth_headers_a,
    )
    assert resp_a.status_code == 201

    resp_b = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_b.id}/subscribers",
        json={"email": email, "first_name": "User B sub"},
        headers=auth_headers_b,
    )
    assert resp_b.status_code == 201


@pytest.mark.asyncio
async def test_list_subscribers_pagination_and_filters(
    async_client: AsyncClient,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """Test paginated retrieval and status/search filters for subscribers."""
    # Seed 12 active and 3 unsubscribed subscribers
    for i in range(12):
        await async_client.post(
            f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
            json={
                "email": f"active{i:02d}@example.com",
                "first_name": f"ActiveName{i}",
                "status": "active",
            },
            headers=auth_headers_a,
        )
    for i in range(3):
        await async_client.post(
            f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
            json={
                "email": f"unsub{i:02d}@example.com",
                "first_name": f"UnsubName{i}",
                "status": "unsubscribed",
            },
            headers=auth_headers_a,
        )

    # 1. Pagination check
    resp_p1 = await async_client.get(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers?page=1&page_size=10",
        headers=auth_headers_a,
    )
    assert resp_p1.status_code == 200
    data_p1 = resp_p1.json()
    assert len(data_p1["items"]) == 10
    assert data_p1["total"] == 15
    assert data_p1["total_pages"] == 2

    # 2. Status filter check
    resp_unsub = await async_client.get(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers?status=unsubscribed",
        headers=auth_headers_a,
    )
    assert resp_unsub.status_code == 200
    assert resp_unsub.json()["total"] == 3

    # 3. Search query check
    resp_search = await async_client.get(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers?search=active05",
        headers=auth_headers_a,
    )
    assert resp_search.status_code == 200
    assert resp_search.json()["total"] == 1
    assert resp_search.json()["items"][0]["email"] == "active05@example.com"


@pytest.mark.asyncio
async def test_get_subscriber_by_id(
    async_client: AsyncClient,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """Test retrieving single subscriber by ID."""
    created_resp = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        json={"email": "target@example.com", "first_name": "Target"},
        headers=auth_headers_a,
    )
    sub_id = created_resp.json()["id"]

    get_resp = await async_client.get(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers/{sub_id}",
        headers=auth_headers_a,
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == sub_id


@pytest.mark.asyncio
async def test_update_subscriber(
    async_client: AsyncClient,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """Test updating subscriber details (fields, status, metadata)."""
    created_resp = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        json={"email": "original@example.com", "status": "active"},
        headers=auth_headers_a,
    )
    sub_id = created_resp.json()["id"]

    update_payload = {
        "email": "updated@example.com",
        "first_name": "UpdatedFirst",
        "last_name": "UpdatedLast",
        "status": "unsubscribed",
        "metadata": {"updated": True},
    }
    patch_resp = await async_client.patch(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers/{sub_id}",
        json=update_payload,
        headers=auth_headers_a,
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["email"] == "updated@example.com"
    assert data["first_name"] == "UpdatedFirst"
    assert data["status"] == "unsubscribed"
    assert data["metadata"] == {"updated": True}


@pytest.mark.asyncio
async def test_update_subscriber_conflict(
    async_client: AsyncClient,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """Test updating subscriber email to an existing email in same list returns 409."""
    await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        json={"email": "existing@example.com"},
        headers=auth_headers_a,
    )
    created_resp = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        json={"email": "current@example.com"},
        headers=auth_headers_a,
    )
    sub_id = created_resp.json()["id"]

    patch_resp = await async_client.patch(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers/{sub_id}",
        json={"email": "existing@example.com"},
        headers=auth_headers_a,
    )
    assert patch_resp.status_code == 409


@pytest.mark.asyncio
async def test_delete_subscriber(
    async_client: AsyncClient,
    contact_list_a: ContactList,
    auth_headers_a: Dict[str, str],
):
    """Test deleting subscriber returns 204 No Content."""
    created_resp = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        json={"email": "to_delete@example.com"},
        headers=auth_headers_a,
    )
    sub_id = created_resp.json()["id"]

    del_resp = await async_client.delete(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers/{sub_id}",
        headers=auth_headers_a,
    )
    assert del_resp.status_code == 204

    get_resp = await async_client.get(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers/{sub_id}",
        headers=auth_headers_a,
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_cross_user_subscriber_access_rejected(
    async_client: AsyncClient,
    contact_list_a: ContactList,
    contact_list_b: ContactList,
    auth_headers_a: Dict[str, str],
    auth_headers_b: Dict[str, str],
):
    """
    CRITICAL: User A attempts to read, mutate or delete User B's subscribers.
    Must return 404 Not Found.
    """
    # Create subscriber in User B's list
    sub_b_resp = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_b.id}/subscribers",
        json={"email": "userb_sub@example.com"},
        headers=auth_headers_b,
    )
    sub_b_id = sub_b_resp.json()["id"]

    # User A attempts GET on User B's subscriber via User B's list
    resp1 = await async_client.get(
        f"/api/v1/contact-lists/{contact_list_b.id}/subscribers/{sub_b_id}",
        headers=auth_headers_a,
    )
    assert resp1.status_code == 404

    # User A attempts GET on User B's subscriber via User A's list (ID manipulation)
    resp2 = await async_client.get(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers/{sub_b_id}",
        headers=auth_headers_a,
    )
    assert resp2.status_code == 404

    # User A attempts PATCH on User B's subscriber
    resp3 = await async_client.patch(
        f"/api/v1/contact-lists/{contact_list_b.id}/subscribers/{sub_b_id}",
        json={"first_name": "Hacked"},
        headers=auth_headers_a,
    )
    assert resp3.status_code == 404

    # User A attempts DELETE on User B's subscriber
    resp4 = await async_client.delete(
        f"/api/v1/contact-lists/{contact_list_b.id}/subscribers/{sub_b_id}",
        headers=auth_headers_a,
    )
    assert resp4.status_code == 404
