import io
from unittest.mock import patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.contact_list import ContactList
from app.models.import_job import ImportError, ImportJob
from app.models.user import User


@pytest.mark.asyncio
async def test_import_subscribers_csv_success(
    async_client: AsyncClient,
    auth_headers_a: dict,
    contact_list_a: ContactList,
):
    csv_content = b"email,first_name,last_name\nalice@example.com,Alice,Smith\nbob@example.com,Bob,Jones\n"
    files = {"file": ("subscribers.csv", io.BytesIO(csv_content), "text/csv")}

    response = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers/import",
        files=files,
        headers=auth_headers_a,
    )

    assert response.status_code == 202
    data = response.json()
    assert "import_id" in data
    assert data["status"] == "queued"
    assert data["message"] == "Subscriber import queued successfully"


@pytest.mark.asyncio
async def test_import_subscribers_invalid_file_extension(
    async_client: AsyncClient,
    auth_headers_a: dict,
    contact_list_a: ContactList,
):
    files = {"file": ("payload.exe", io.BytesIO(b"malicious content"), "application/octet-stream")}

    response = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers/import",
        files=files,
        headers=auth_headers_a,
    )

    assert response.status_code == 400
    assert "must be a CSV file" in response.json()["detail"]


@pytest.mark.asyncio
async def test_import_subscribers_unauthenticated(
    async_client: AsyncClient,
    contact_list_a: ContactList,
):
    files = {"file": ("subscribers.csv", io.BytesIO(b"email\ntest@example.com"), "text/csv")}

    response = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers/import",
        files=files,
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_import_subscribers_cross_user_rejected(
    async_client: AsyncClient,
    auth_headers_b: dict,
    contact_list_a: ContactList,
):
    files = {"file": ("subscribers.csv", io.BytesIO(b"email\ntest@example.com"), "text/csv")}

    # User B attempts to upload CSV to User A's list
    response = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers/import",
        files=files,
        headers=auth_headers_b,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Contact list not found"


@pytest.mark.asyncio
async def test_get_import_job_status_success(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers_a: dict,
    user_a: User,
    contact_list_a: ContactList,
):
    job = ImportJob(
        owner_id=user_a.id,
        contact_list_id=contact_list_a.id,
        status="completed",
        original_filename="audience.csv",
        file_path="uploads/imports/dummy.csv",
        total_rows=100,
        processed_rows=100,
        imported_rows=95,
        skipped_rows=5,
        duplicate_rows=3,
        invalid_rows=2,
        error_count=5,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    response = await async_client.get(
        f"/api/v1/imports/{job.id}",
        headers=auth_headers_a,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(job.id)
    assert data["status"] == "completed"
    assert data["imported_rows"] == 95
    assert data["duplicate_rows"] == 3
    assert data["invalid_rows"] == 2
    assert data["error_count"] == 5


@pytest.mark.asyncio
async def test_get_import_job_cross_user_rejected(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers_b: dict,
    user_a: User,
    contact_list_a: ContactList,
):
    job = ImportJob(
        owner_id=user_a.id,
        contact_list_id=contact_list_a.id,
        status="queued",
        original_filename="secret.csv",
        file_path="uploads/imports/secret.csv",
    )
    db_session.add(job)
    await db_session.commit()

    # User B requests User A's import job
    response = await async_client.get(
        f"/api/v1/imports/{job.id}",
        headers=auth_headers_b,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Import job not found"


@pytest.mark.asyncio
async def test_list_import_errors_success(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers_a: dict,
    user_a: User,
    contact_list_a: ContactList,
):
    job = ImportJob(
        owner_id=user_a.id,
        contact_list_id=contact_list_a.id,
        status="completed",
        original_filename="bad_rows.csv",
        file_path="uploads/imports/dummy.csv",
        error_count=2,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    err1 = ImportError(
        import_job_id=job.id,
        row_number=5,
        error_type="INVALID_EMAIL",
        message="Invalid email syntax",
    )
    err2 = ImportError(
        import_job_id=job.id,
        row_number=12,
        error_type="DUPLICATE_IN_FILE",
        message="Duplicate email in CSV",
    )
    db_session.add_all([err1, err2])
    await db_session.commit()

    response = await async_client.get(
        f"/api/v1/imports/{job.id}/errors?page=1&page_size=10",
        headers=auth_headers_a,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["row_number"] == 5
    assert data["items"][0]["error_type"] == "INVALID_EMAIL"
    assert data["items"][1]["row_number"] == 12
    assert data["items"][1]["error_type"] == "DUPLICATE_IN_FILE"


@pytest.mark.asyncio
async def test_list_import_errors_cross_user_rejected(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers_b: dict,
    user_a: User,
    contact_list_a: ContactList,
):
    job = ImportJob(
        owner_id=user_a.id,
        contact_list_id=contact_list_a.id,
        status="completed",
        original_filename="audience.csv",
        file_path="uploads/imports/dummy.csv",
    )
    db_session.add(job)
    await db_session.commit()

    response = await async_client.get(
        f"/api/v1/imports/{job.id}/errors",
        headers=auth_headers_b,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Import job not found"


@pytest.mark.asyncio
async def test_import_subscribers_redis_failure_handled(
    async_client: AsyncClient,
    auth_headers_a: dict,
    contact_list_a: ContactList,
):
    with patch("app.services.import_service.process_subscriber_import.delay") as mock_delay:
        mock_delay.side_effect = Exception("Redis broker down")

        csv_content = b"email\ntest@example.com\n"
        files = {"file": ("subscribers.csv", io.BytesIO(csv_content), "text/csv")}

        response = await async_client.post(
            f"/api/v1/contact-lists/{contact_list_a.id}/subscribers/import",
            files=files,
            headers=auth_headers_a,
        )

        assert response.status_code == 503
        assert "Background task broker is currently unavailable" in response.json()["detail"]
