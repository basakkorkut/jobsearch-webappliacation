import logging
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import rabbitmq as rmq
from app.core.redis_client import get_redis
from app.repositories import application_repository, job_repository, user_profile_repository
from app.schemas.job_posting import JobPostingCreate, JobPostingListItem, JobPostingResponse, JobPostingUpdate
from app.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)

_JOB_KEY = "job:posting:{id}"
_CITY_KEY = "jobs:city:{city}:recent"


async def _invalidate_job_caches(job_id: uuid.UUID, city: str) -> None:
    try:
        redis = get_redis()
        await redis.delete(_JOB_KEY.format(id=str(job_id)))
        await redis.delete(_CITY_KEY.format(city=city.lower()))
    except Exception as exc:
        logger.warning("Cache invalidation failed: %s", exc)


async def get_job_detail(session: AsyncSession, job_id: uuid.UUID) -> JobPostingResponse:
    redis = get_redis()
    key = _JOB_KEY.format(id=str(job_id))

    try:
        cached = await redis.get(key)
        if cached:
            return JobPostingResponse.model_validate_json(cached)
    except Exception as exc:
        logger.warning("Redis get failed: %s", exc)

    job = await job_repository.get_by_id(session, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    response = JobPostingResponse.model_validate(job)
    try:
        await redis.set(key, response.model_dump_json(), ex=3600)
    except Exception as exc:
        logger.warning("Redis set failed: %s", exc)

    return response


async def list_jobs(
    session: AsyncSession,
    city: Optional[str],
    country: Optional[str],
    page: int,
    limit: int,
) -> PaginatedResponse:
    jobs, total = await job_repository.list_jobs(session, city, country, page, limit)
    items = [JobPostingListItem.model_validate(j) for j in jobs]
    return PaginatedResponse.build(items=items, total=total, page=page, limit=limit)


async def get_related_jobs(session: AsyncSession, job_id: uuid.UUID) -> list[JobPostingListItem]:
    job = await job_repository.get_by_id(session, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    related = await job_repository.get_related(session, job, limit=3)
    return [JobPostingListItem.model_validate(j) for j in related]


async def create_job(
    session: AsyncSession,
    data: JobPostingCreate,
    user_id: str,
) -> JobPostingResponse:
    role = await user_profile_repository.get_role(session, uuid.UUID(user_id))
    if role not in ("admin", "company"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin/company users can create jobs")

    job = await job_repository.create_job(
        session,
        company_id=data.company_id,
        title=data.title,
        description=data.description,
        country=data.country,
        city=data.city,
        town=data.town,
        working_preference=data.working_preference,
        position_level=data.position_level,
        department=data.department,
        employment_type=data.employment_type,
        created_by=uuid.UUID(user_id),
    )

    # Invalidate city cache
    try:
        redis = get_redis()
        await redis.delete(_CITY_KEY.format(city=data.city.lower()))
    except Exception as exc:
        logger.warning("Cache invalidation failed: %s", exc)

    # Publish to RabbitMQ
    try:
        await rmq.publish_job_created({
            "job_posting_id": str(job.id),
            "title": job.title,
            "country": job.country,
            "city": job.city,
            "town": job.town,
            "working_preference": job.working_preference,
            "department": job.department,
            "created_at": job.created_at.isoformat(),
        })
    except Exception as exc:
        logger.warning("RabbitMQ publish failed: %s", exc)

    return JobPostingResponse.model_validate(job)


async def update_job(
    session: AsyncSession,
    job_id: uuid.UUID,
    data: JobPostingUpdate,
    user_id: str,
) -> JobPostingResponse:
    job = await job_repository.get_by_id(session, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    role = await user_profile_repository.get_role(session, uuid.UUID(user_id))
    is_owner = job.created_by == uuid.UUID(user_id)
    if not is_owner and role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorised to update this job")

    update_data = data.model_dump(exclude_none=True)
    updated = await job_repository.update_job(session, job, update_data)
    await _invalidate_job_caches(job_id, updated.city)
    return JobPostingResponse.model_validate(updated)


async def delete_job(session: AsyncSession, job_id: uuid.UUID, user_id: str) -> None:
    job = await job_repository.get_by_id(session, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    role = await user_profile_repository.get_role(session, uuid.UUID(user_id))
    is_owner = job.created_by == uuid.UUID(user_id)
    if not is_owner and role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorised to delete this job")

    city = job.city
    await job_repository.delete_job(session, job)
    await _invalidate_job_caches(job_id, city)


async def apply_to_job(session: AsyncSession, job_id: uuid.UUID, user_id: str) -> dict:
    job = await job_repository.get_by_id(session, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    try:
        app_obj = await application_repository.apply(session, uuid.UUID(user_id), job_id)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already applied to this job")

    # Invalidate cached job detail (application_count changed)
    await _invalidate_job_caches(job_id, job.city)

    return {"job_posting_id": str(job_id), "applied_at": app_obj.applied_at.isoformat()}
