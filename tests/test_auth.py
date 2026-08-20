import pytest
from httpx import AsyncClient
from app.core.security import verify_password
from app.models.user import User


@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient):
    """Test successful user registration."""
    payload = {
        "email": "newuser@example.com",
        "password": "SecurePassword123!",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert "id" in data
    assert "password_hash" not in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient, user_a: User):
    """Test registration with existing email returns 409 Conflict."""
    payload = {
        "email": user_a.email,
        "password": "AnotherPassword123!",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert "already registered" in data["detail"].lower()


@pytest.mark.asyncio
async def test_register_validation_errors(async_client: AsyncClient):
    """Test registration input validation for invalid email and short password."""
    # Invalid email
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "Password123!"},
    )
    assert response.status_code == 422

    # Password too short (< 8 chars)
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "valid@example.com", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, user_a: User):
    """Test successful login returns valid JWT token."""
    payload = {
        "email": user_a.email,
        "password": "Password123!",
    }
    response = await async_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient, user_a: User):
    """Test login with incorrect password returns 401 Unauthorized."""
    payload = {
        "email": user_a.email,
        "password": "WrongPassword!",
    }
    response = await async_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    """Test login with nonexistent email returns 401 Unauthorized."""
    payload = {
        "email": "nonexistent@example.com",
        "password": "Password123!",
    }
    response = await async_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_inactive_user(async_client: AsyncClient, inactive_user: User):
    """Test login with inactive user account returns 401."""
    payload = {
        "email": inactive_user.email,
        "password": "Password123!",
    }
    response = await async_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_password_hashing_security(user_a: User):
    """Test that password hash is securely generated and never equal to plaintext."""
    assert user_a.password_hash != "Password123!"
    assert verify_password("Password123!", user_a.password_hash) is True
    assert verify_password("WrongPassword!", user_a.password_hash) is False
