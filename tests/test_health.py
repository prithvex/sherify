import pytest
from unittest.mock import AsyncMock
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.main import app


@pytest.mark.asyncio
async def test_app_metadata():
    """Verify application startup configuration and metadata."""
    assert app.title == settings.APP_NAME
    assert app.version == "0.1.0"


@pytest.mark.asyncio
async def test_root_health_endpoint(async_client: AsyncClient):
    """Verify GET /health response structure and database probe."""
    response = await async_client.get("/health")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "version" in data
    assert data["version"] == "0.1.0"
    assert data["app_name"] == settings.APP_NAME


@pytest.mark.asyncio
async def test_v1_health_endpoint(async_client: AsyncClient):
    """Verify GET /api/v1/health response structure and database probe."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "version" in data
    assert data["version"] == "0.1.0"
    assert data["app_name"] == settings.APP_NAME


@pytest.mark.asyncio
async def test_health_check_database_failure():
    """Verify health endpoints gracefully report degraded status when database is unreachable."""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute.side_effect = ConnectionRefusedError("Database connection failed")

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            root_resp = await client.get("/health")
            assert root_resp.status_code == 503
            root_data = root_resp.json()
            assert root_data["status"] == "degraded"
            assert root_data["database"] == "unreachable"

            v1_resp = await client.get("/api/v1/health")
            assert v1_resp.status_code == 503
            v1_data = v1_resp.json()
            assert v1_data["status"] == "degraded"
            assert v1_data["database"] == "unreachable"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_database_session_dependency_wiring():
    """Verify canonical get_db dependency yields a functional AsyncSession."""
    async for session in get_db():
        assert isinstance(session, AsyncSession)
        assert session.is_active
        break
