from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.import_job import ImportJob


class ImportJobRepository:
    async def get_by_id(
        self,
        db: AsyncSession,
        job_id: UUID,
        owner_id: Optional[UUID] = None,
    ) -> Optional[ImportJob]:
        stmt = select(ImportJob).where(ImportJob.id == job_id)
        if owner_id is not None:
            stmt = stmt.where(ImportJob.owner_id == owner_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, job: ImportJob) -> ImportJob:
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    async def update(self, db: AsyncSession, job: ImportJob) -> ImportJob:
        await db.commit()
        await db.refresh(job)
        return job

    async def list_by_owner(
        self,
        db: AsyncSession,
        owner_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ImportJob], int]:
        count_query = select(func.count(ImportJob.id)).where(ImportJob.owner_id == owner_id)
        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        offset = (page - 1) * page_size
        stmt = (
            select(ImportJob)
            .where(ImportJob.owner_id == owner_id)
            .order_by(ImportJob.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total


import_job_repository = ImportJobRepository()
