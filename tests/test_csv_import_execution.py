import os
import tempfile
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.contact_list import ContactList
from app.models.import_job import ImportJob
from app.models.subscriber import Subscriber
from app.models.user import User
from app.repositories.import_error_repo import import_error_repository
from app.repositories.import_job_repo import import_job_repository
from app.repositories.subscriber_repo import subscriber_repository
from app.services.import_execution_service import import_execution_service


@pytest.mark.asyncio
async def test_import_execution_scenario_all_valid(
    db_session: AsyncSession,
    user_a: User,
    contact_list_a: ContactList,
):
    # Prepare CSV file on disk
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("email,first_name,last_name\n")
        for i in range(25):
            f.write(f"bulk_user_{i:03d}@example.com,First{i},Last{i}\n")
        temp_path = f.name

    job = ImportJob(
        owner_id=user_a.id,
        contact_list_id=contact_list_a.id,
        status="queued",
        original_filename="valid_subscribers.csv",
        file_path=temp_path,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    # Execute import
    await import_execution_service.execute_import(job_id=job.id, db=db_session)

    # Refresh and inspect job
    await db_session.refresh(job)
    assert job.status == "completed"
    assert job.imported_rows == 25
    assert job.duplicate_rows == 0
    assert job.invalid_rows == 0
    assert job.error_count == 0
    assert job.processed_rows == 25

    # Verify subscribers in database
    subs, total = await subscriber_repository.list_by_contact_list(
        db_session, contact_list_id=contact_list_a.id, page_size=100
    )
    assert total == 25

    # Verify file was cleaned up
    assert not os.path.exists(temp_path)


@pytest.mark.asyncio
async def test_import_execution_scenario_mixed_with_invalid_and_duplicates(
    db_session: AsyncSession,
    user_a: User,
    contact_list_a: ContactList,
):
    # Pre-create 1 subscriber in database to test DUPLICATE_IN_LIST
    existing_sub = Subscriber(
        contact_list_id=contact_list_a.id,
        email="existing_user@example.com",
        first_name="PreExisting",
        status="active",
    )
    db_session.add(existing_sub)
    await db_session.commit()

    # CSV containing:
    # 3 valid emails
    # 2 malformed emails
    # 1 empty email
    # 1 in-file duplicate
    # 1 in-list duplicate (existing_user@example.com)
    csv_data = """email,first_name,last_name
valid1@example.com,Alice,Smith
invalid-email-no-at,Bad,User
valid2@example.com,Bob,Jones
,NoEmail,User
valid1@example.com,AliceDuplicate,Smith
existing_user@example.com,Pre,Existing
valid3@example.com,Charlie,Brown
bad@domain..invalid,BadDomain,User
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_data)
        temp_path = f.name

    job = ImportJob(
        owner_id=user_a.id,
        contact_list_id=contact_list_a.id,
        status="queued",
        original_filename="mixed.csv",
        file_path=temp_path,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    # Execute import
    await import_execution_service.execute_import(job_id=job.id, db=db_session)

    # Inspect job
    await db_session.refresh(job)
    assert job.status == "completed"
    assert job.imported_rows == 3  # valid1, valid2, valid3
    assert job.duplicate_rows == 2  # 1 in-file duplicate + 1 in-list duplicate
    assert job.invalid_rows == 3  # invalid-email-no-at, empty email, bad@domain..invalid
    assert job.error_count == 5
    assert job.processed_rows == 8

    # Verify error records
    errors, err_count = await import_error_repository.list_by_job(db_session, job_id=job.id, page_size=50)
    assert err_count == 5
    error_types = [e.error_type for e in errors]
    assert "INVALID_EMAIL" in error_types
    assert "EMPTY_EMAIL" in error_types
    assert "DUPLICATE_IN_FILE" in error_types
    assert "DUPLICATE_IN_LIST" in error_types


@pytest.mark.asyncio
async def test_import_execution_missing_email_header_fails(
    db_session: AsyncSession,
    user_a: User,
    contact_list_a: ContactList,
):
    # CSV without email header
    csv_data = """first_name,last_name,phone
Alice,Smith,555-0199
Bob,Jones,555-0198
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_data)
        temp_path = f.name

    job = ImportJob(
        owner_id=user_a.id,
        contact_list_id=contact_list_a.id,
        status="queued",
        original_filename="no_email_header.csv",
        file_path=temp_path,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    # Execute import
    await import_execution_service.execute_import(job_id=job.id, db=db_session)

    await db_session.refresh(job)
    assert job.status == "failed"
    assert job.error_count == 1

    errors, _ = await import_error_repository.list_by_job(db_session, job_id=job.id)
    assert len(errors) == 1
    assert errors[0].error_type == "MISSING_EMAIL_HEADER"


@pytest.mark.asyncio
async def test_import_execution_csv_formatting_edge_cases(
    db_session: AsyncSession,
    user_a: User,
    contact_list_a: ContactList,
):
    # Test UTF-8 BOM, column reordering, whitespace, uppercase emails, and quoted commas
    csv_data = (
        "\ufefflast_name,first_name,email\n"
        'Smith,  Alice  ,  ALICE.EDGE@EXAMPLE.COM  \n'
        '"Jones, Jr.",Bob,bob.jones@example.com\n'
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig") as f:
        f.write(csv_data)
        temp_path = f.name

    job = ImportJob(
        owner_id=user_a.id,
        contact_list_id=contact_list_a.id,
        status="queued",
        original_filename="edge_cases.csv",
        file_path=temp_path,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    # Execute import
    await import_execution_service.execute_import(job_id=job.id, db=db_session)

    await db_session.refresh(job)
    assert job.status == "completed"
    assert job.imported_rows == 2
    assert job.error_count == 0

    sub_alice = await subscriber_repository.get_by_email(
        db_session, contact_list_id=contact_list_a.id, email="alice.edge@example.com"
    )
    assert sub_alice is not None
    assert sub_alice.first_name == "Alice"
    assert sub_alice.last_name == "Smith"

    sub_bob = await subscriber_repository.get_by_email(
        db_session, contact_list_id=contact_list_a.id, email="bob.jones@example.com"
    )
    assert sub_bob is not None
    assert sub_bob.first_name == "Bob"
    assert sub_bob.last_name == "Jones, Jr."


@pytest.mark.asyncio
async def test_import_execution_idempotency_and_retry_safety(
    db_session: AsyncSession,
    user_a: User,
    contact_list_a: ContactList,
):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("email,first_name\nretry_user@example.com,RetryUser\n")
        temp_path = f.name

    job = ImportJob(
        owner_id=user_a.id,
        contact_list_id=contact_list_a.id,
        status="queued",
        original_filename="retry_test.csv",
        file_path=temp_path,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    # First execution
    await import_execution_service.execute_import(job_id=job.id, db=db_session)
    await db_session.refresh(job)
    assert job.status == "completed"
    assert job.imported_rows == 1

    # Second execution (e.g. accidental duplicate Celery delivery)
    await import_execution_service.execute_import(job_id=job.id, db=db_session)
    await db_session.refresh(job)
    assert job.status == "completed"

    # Subscriber count in list should still be exactly 1
    _, total = await subscriber_repository.list_by_contact_list(db_session, contact_list_id=contact_list_a.id)
    assert total == 1
