import csv
import io
import logging
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List, Optional, Set, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.import_job import ImportError, ImportJob
from app.models.subscriber import Subscriber
from app.repositories.import_error_repo import import_error_repository
from app.repositories.import_job_repo import import_job_repository
from app.repositories.subscriber_repo import subscriber_repository
from app.schemas.import_job import ImportStatus
from app.storage import get_file_storage

logger = logging.getLogger(__name__)

# Basic robust syntactic email validation pattern
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


@asynccontextmanager
async def _get_session(db: Optional[AsyncSession] = None) -> AsyncGenerator[AsyncSession, None]:
    if db is not None:
        yield db
    else:
        async with AsyncSessionLocal() as session:
            yield session


class ImportExecutionService:
    """
    Background worker service that parses CSV files in streaming batches and safely inserts subscribers.
    """

    def _normalize_email(self, email: str) -> str:
        return email.strip().lower()

    def _is_valid_email(self, email: str) -> bool:
        if not email or len(email) > 255:
            return False
        if not EMAIL_REGEX.match(email):
            return False
        # Disallow trailing dots or double dots in domain
        domain = email.split("@")[-1]
        if domain.startswith(".") or domain.endswith(".") or ".." in domain:
            return False
        return True

    def _map_headers(self, raw_headers: List[str]) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """
        Normalize header names and find column indexes for email, first_name, and last_name.
        """
        email_idx = None
        first_name_idx = None
        last_name_idx = None

        for idx, h in enumerate(raw_headers):
            clean_header = h.strip().lower().lstrip("\ufeff")  # strip BOM
            if clean_header in ["email", "e-mail", "email_address", "mail"]:
                email_idx = idx
            elif clean_header in ["first_name", "firstname", "first", "fname"]:
                first_name_idx = idx
            elif clean_header in ["last_name", "lastname", "last", "lname"]:
                last_name_idx = idx

        return email_idx, first_name_idx, last_name_idx

    async def execute_import(
        self,
        job_id: UUID,
        task_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> None:
        """
        Stream and process the CSV file for the specified ImportJob.
        """
        storage = get_file_storage()

        async with _get_session(db) as session:
            # 1. Fetch ImportJob
            job = await import_job_repository.get_by_id(session, job_id=job_id)
            if not job:
                logger.error(f"[Task {task_id}] ImportJob {job_id} not found.")
                return

            if job.status in [ImportStatus.COMPLETED.value, ImportStatus.FAILED.value]:
                logger.info(f"[Task {task_id}] ImportJob {job_id} already in terminal status '{job.status}'.")
                return

            # 2. Transition QUEUED -> PROCESSING
            job.status = ImportStatus.PROCESSING.value
            await session.commit()
            logger.info(f"[Task {task_id}] ImportJob {job_id} transitioned to PROCESSING.")

            file_path = storage.get_file_path(job.file_path)
            batch_size = settings.IMPORT_BATCH_SIZE
            seen_in_file_emails: Set[str] = set()

            try:
                with open(file_path, mode="r", encoding="utf-8-sig", errors="replace") as csv_file:
                    reader = csv.reader(csv_file)
                    
                    # Read Header Row
                    try:
                        header_row = next(reader)
                    except StopIteration:
                        # Empty file
                        job.status = ImportStatus.COMPLETED.value
                        job.completed_at = datetime.now(timezone.utc)
                        await session.commit()
                        storage.delete_file(job.file_path)
                        return

                    email_idx, fn_idx, ln_idx = self._map_headers(header_row)

                    if email_idx is None:
                        err = ImportError(
                            import_job_id=job.id,
                            row_number=1,
                            error_type="MISSING_EMAIL_HEADER",
                            message="CSV header must contain an 'email' column.",
                        )
                        session.add(err)
                        job.status = ImportStatus.FAILED.value
                        job.error_count += 1
                        job.completed_at = datetime.now(timezone.utc)
                        await session.commit()
                        storage.delete_file(job.file_path)
                        return

                    # Row Processing Loop
                    row_num = 1
                    batch_rows: List[Tuple[int, str, Optional[str], Optional[str]]] = []
                    batch_errors: List[ImportError] = []

                    for row in reader:
                        row_num += 1
                        if not row or not any(field.strip() for field in row):
                            # Skip entirely blank lines
                            continue

                        raw_email = row[email_idx].strip() if email_idx < len(row) else ""
                        first_name = row[fn_idx].strip() if (fn_idx is not None and fn_idx < len(row) and row[fn_idx].strip()) else None
                        last_name = row[ln_idx].strip() if (ln_idx is not None and ln_idx < len(row) and row[ln_idx].strip()) else None

                        # Validation: Empty Email
                        if not raw_email:
                            batch_errors.append(
                                ImportError(
                                    import_job_id=job.id,
                                    row_number=row_num,
                                    error_type="EMPTY_EMAIL",
                                    message="Email field is empty.",
                                )
                            )
                            job.invalid_rows += 1
                            job.skipped_rows += 1
                            job.error_count += 1
                            job.processed_rows += 1
                            continue

                        norm_email = self._normalize_email(raw_email)

                        # Validation: Format
                        if not self._is_valid_email(norm_email):
                            batch_errors.append(
                                ImportError(
                                    import_job_id=job.id,
                                    row_number=row_num,
                                    error_type="INVALID_EMAIL",
                                    message=f"Invalid email address format: '{raw_email[:100]}'",
                                )
                            )
                            job.invalid_rows += 1
                            job.skipped_rows += 1
                            job.error_count += 1
                            job.processed_rows += 1
                            continue

                        # Validation: Duplicate in same CSV
                        if norm_email in seen_in_file_emails:
                            batch_errors.append(
                                ImportError(
                                    import_job_id=job.id,
                                    row_number=row_num,
                                    error_type="DUPLICATE_IN_FILE",
                                    message=f"Duplicate email found within CSV file: '{norm_email}'",
                                )
                            )
                            job.duplicate_rows += 1
                            job.skipped_rows += 1
                            job.error_count += 1
                            job.processed_rows += 1
                            continue

                        seen_in_file_emails.add(norm_email)
                        batch_rows.append((row_num, norm_email, first_name, last_name))

                        # If batch size reached, flush batch
                        if len(batch_rows) >= batch_size:
                            await self._flush_batch(
                                session,
                                job=job,
                                batch_rows=batch_rows,
                                batch_errors=batch_errors,
                            )
                            batch_rows = []
                            batch_errors = []

                    # Flush any remaining items in final batch
                    if batch_rows or batch_errors:
                        await self._flush_batch(
                            session,
                            job=job,
                            batch_rows=batch_rows,
                            batch_errors=batch_errors,
                        )

                # Mark Job COMPLETED
                job.total_rows = job.processed_rows
                job.status = ImportStatus.COMPLETED.value
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()
                logger.info(
                    f"[Task {task_id}] ImportJob {job_id} completed: "
                    f"{job.imported_rows} imported, {job.duplicate_rows} duplicates, {job.invalid_rows} invalid."
                )

            except Exception as e:
                logger.error(f"[Task {task_id}] Fatal error executing import for Job {job_id}: {e}", exc_info=True)
                job.status = ImportStatus.FAILED.value
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()
            finally:
                # Clean up stored CSV file
                storage.delete_file(job.file_path)

    async def _flush_batch(
        self,
        db: AsyncSession,
        job: ImportJob,
        batch_rows: List[Tuple[int, str, Optional[str], Optional[str]]],
        batch_errors: List[ImportError],
    ) -> None:
        """
        Process in-database duplicate checks, bulk insert valid subscribers, and commit batch.
        """
        if batch_rows:
            batch_emails = [r[1] for r in batch_rows]
            existing_emails_set = await subscriber_repository.get_existing_emails_set(
                db,
                contact_list_id=job.contact_list_id,
                emails=batch_emails,
            )

            new_subscribers: List[Subscriber] = []
            for row_num, email, first_name, last_name in batch_rows:
                job.processed_rows += 1
                if email in existing_emails_set:
                    batch_errors.append(
                        ImportError(
                            import_job_id=job.id,
                            row_number=row_num,
                            error_type="DUPLICATE_IN_LIST",
                            message=f"Subscriber with email '{email}' already exists in this contact list.",
                        )
                    )
                    job.duplicate_rows += 1
                    job.skipped_rows += 1
                    job.error_count += 1
                else:
                    new_subscribers.append(
                        Subscriber(
                            contact_list_id=job.contact_list_id,
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                            status="active",
                            metadata_json={},
                        )
                    )
                    job.imported_rows += 1

            if new_subscribers:
                await subscriber_repository.bulk_create(db, new_subscribers)

        if batch_errors:
            await import_error_repository.bulk_create(db, batch_errors)

        # Update Job Progress in DB
        await db.commit()


import_execution_service = ImportExecutionService()
