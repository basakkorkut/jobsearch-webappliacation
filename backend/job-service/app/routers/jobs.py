import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.schemas.job_posting import JobPostingCreate, JobPostingListItem, JobPostingResponse, JobPostingUpdate
from app.schemas.common import PaginatedResponse
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=PaginatedResponse)
async def list_jobs(
    city: str | None = Query(None),
    country: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await job_service.list_jobs(db, city, country, page, limit)


@router.get("/{job_id}/related", response_model=list[JobPostingListItem])
async def get_related_jobs(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await job_service.get_related_jobs(db, job_id)


@router.get("/{job_id}", response_model=JobPostingResponse)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await job_service.get_job_detail(db, job_id)


@router.post("", response_model=JobPostingResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    body: JobPostingCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await job_service.create_job(db, body, current_user.id)


@router.put("/{job_id}", response_model=JobPostingResponse)
async def update_job(
    job_id: uuid.UUID,
    body: JobPostingUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await job_service.update_job(db, job_id, body, current_user.id)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await job_service.delete_job(db, job_id, current_user.id)


@router.post("/{job_id}/apply", status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    job_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await job_service.apply_to_job(db, job_id, current_user.id)
