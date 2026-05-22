from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user, get_optional_user
from app.core.database import get_db
from app.schemas.job_posting import JobPostingListItem
from app.schemas.common import PaginatedResponse
from app.services import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=PaginatedResponse)
async def search_jobs(
    position: str | None = Query(None),
    country: str | None = Query(None),
    city: str | None = Query(None),
    town: str | None = Query(None),
    working_preference: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.id if current_user else None
    return await search_service.search_jobs(
        db, position, country, city, town, working_preference, page, limit, user_id
    )


@router.get("/recent")
async def recent_searches(
    current_user: CurrentUser = Depends(get_current_user),
):
    return await search_service.get_recent_searches(current_user.id)


@router.get("/autocomplete/positions")
async def autocomplete_positions(
    q: str = Query("", min_length=0),
    db: AsyncSession = Depends(get_db),
):
    return await search_service.autocomplete_positions(db, q)


@router.get("/autocomplete/cities")
async def autocomplete_cities(
    q: str = Query("", min_length=0),
    db: AsyncSession = Depends(get_db),
):
    return await search_service.autocomplete_cities(db, q)


@router.get("/featured", response_model=list[JobPostingListItem])
async def featured_jobs(
    city: str = Query(..., description="City name for featured jobs"),
    db: AsyncSession = Depends(get_db),
):
    return await search_service.get_featured_jobs(db, city)
