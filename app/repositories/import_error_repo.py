from typing import List, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.import_job import ImportError


class ImportErrorRepository:
    async def bulk_create(
        self,
        db: AsyncSession,
        errors: List[ImportError],
    ) -> None:
        """
        Add a batch of ImportError records.
        """
        db.add_all(errors)
        await db.flush()

    async def list_by_job(
        self,
        db: AsyncSession,
        job_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ImportError], int]:
        count_query = select(func.count(ImportError.id)).where(ImportError.import_job_id == job_id)
        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        offset = (page - 1) * page_size
        stmt = (
            select(ImportError)
            .where(ImportError.import_job_id == job_id)
            .order_by(ImportError.row_number.asc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total


import_error_repository = ImportErrorRepository()
