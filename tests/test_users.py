from typing import Dict
import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.asyncio
async def test_get_current_user_profile_success(
    async_client: AsyncClient,
    user_a: User,
    auth_headers_a: Dict[str, str],
):
    """Test GET /api/v1/users/me returns authenticated user's profile."""
    response = await async_client.get("/api/v1/users/me", headers=auth_headers_a)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user_a.id)
    assert data["email"] == user_a.email
    assert data["is_active"] is True
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(async_client: AsyncClient):
    """Test GET /api/v1/users/me without token returns 401 Unauthorized."""
    response = await async_client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(async_client: AsyncClient):
    """Test GET /api/v1/users/me with invalid/tampered token returns 401."""
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    response = await async_client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_inactive(
    async_client: AsyncClient,
    inactive_auth_headers: Dict[str, str],
):
    """Test GET /api/v1/users/me with inactive user returns 401."""
    response = await async_client.get("/api/v1/users/me", headers=inactive_auth_headers)
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()
