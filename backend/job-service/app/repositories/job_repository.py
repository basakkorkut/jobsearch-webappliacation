import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_posting import JobPosting


async def get_by_id(session: AsyncSession, job_id: uuid.UUID) -> Optional[JobPosting]:
    result = await session.execute(select(JobPosting).where(JobPosting.id == job_id))
    return result.scalar_one_or_none()


async def list_jobs(
    session: AsyncSession,
    city: Optional[str],
    country: Optional[str],
    page: int,
    limit: int,
) -> tuple[list[JobPosting], int]:
    stmt = select(JobPosting)
    if city:
        stmt = stmt.where(JobPosting.city.ilike(f"%{city}%"))
    if country:
        stmt = stmt.where(JobPosting.country.ilike(f"%{country}%"))

    total: int = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(JobPosting.created_at.desc()).offset((page - 1) * limit).limit(limit)
    rows = await session.execute(stmt)
    return list(rows.scalars().all()), total


async def search_jobs(
    session: AsyncSession,
    position: Optional[str],
    country: Optional[str],
    city: Optional[str],
    town: Optional[str],
    working_preference: Optional[str],
    page: int,
    limit: int,
) -> tuple[list[JobPosting], int]:
    stmt = select(JobPosting)
    if position:
        stmt = stmt.where(JobPosting.title.ilike(f"%{position}%"))
    if country:
        stmt = stmt.where(JobPosting.country.ilike(f"%{country}%"))
    if city:
        stmt = stmt.where(JobPosting.city.ilike(f"%{city}%"))
    if town:
        stmt = stmt.where(JobPosting.town.ilike(f"%{town}%"))
    if working_preference:
        stmt = stmt.where(JobPosting.working_preference == working_preference)

    total: int = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(JobPosting.created_at.desc()).offset((page - 1) * limit).limit(limit)
    rows = await session.execute(stmt)
    return list(rows.scalars().all()), total


async def get_related(session: AsyncSession, job: JobPosting, limit: int = 3) -> list[JobPosting]:
    first_word = job.title.split()[0] if job.title.split() else job.title
    stmt = (
        select(JobPosting)
        .where(JobPosting.city == job.city)
        .where(JobPosting.id != job.id)
        .where(JobPosting.title.ilike(f"%{first_word}%"))
        .limit(limit)
    )
    rows = await session.execute(stmt)
    related = list(rows.scalars().all())

    if len(related) < limit:
        exclude_ids = [j.id for j in related] + [job.id]
        stmt2 = (
            select(JobPosting)
            .where(JobPosting.city == job.city)
            .where(~JobPosting.id.in_(exclude_ids))
            .limit(limit - len(related))
        )
        rows2 = await session.execute(stmt2)
        related.extend(rows2.scalars().all())

    return related


async def get_by_city(session: AsyncSession, city: str, limit: int = 5) -> list[JobPosting]:
    rows = await session.execute(
        select(JobPosting)
        .where(JobPosting.city.ilike(city))
        .order_by(JobPosting.created_at.desc())
        .limit(limit)
    )
    return list(rows.scalars().all())


async def autocomplete_positions(session: AsyncSession, prefix: str, limit: int = 10) -> list[str]:
    rows = await session.execute(
        select(JobPosting.title).where(JobPosting.title.ilike(f"{prefix}%")).distinct().limit(limit)
    )
    return [r[0] for r in rows.all()]


async def autocomplete_cities(session: AsyncSession, prefix: str, limit: int = 10) -> list[str]:
    rows = await session.execute(
        select(JobPosting.city).where(JobPosting.city.ilike(f"{prefix}%")).distinct().limit(limit)
    )
    return [r[0] for r in rows.all()]


async def create_job(session: AsyncSession, **data) -> JobPosting:
    job = JobPosting(**data)
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def update_job(session: AsyncSession, job: JobPosting, data: dict) -> JobPosting:
    for key, value in data.items():
        setattr(job, key, value)
    await session.commit()
    await session.refresh(job)
    return job


async def delete_job(session: AsyncSession, job: JobPosting) -> None:
    await session.delete(job)
    await session.commit()
