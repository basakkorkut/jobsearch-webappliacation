import asyncio
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mongodb import get_mongodb
from app.core.redis_client import get_redis
from app.repositories import job_repository, search_repository
from app.schemas.job_posting import JobPostingListItem
from app.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)

_AUTO_POS = "autocomplete:position:{prefix}"
_AUTO_CITY = "autocomplete:city:{prefix}"
_FEATURED = "jobs:city:{city}:recent"


async def search_jobs(
    session: AsyncSession,
    position: Optional[str],
    country: Optional[str],
    city: Optional[str],
    town: Optional[str],
    working_preference: Optional[str],
    page: int,
    limit: int,
    user_id: Optional[str],
) -> PaginatedResponse:
    jobs, total = await job_repository.search_jobs(
        session, position, country, city, town, working_preference, page, limit
    )

    # Fire-and-forget: log to MongoDB (don't block response)
    db = get_mongodb()
    asyncio.create_task(
        search_repository.log_search(
            db=db,
            user_id=user_id or "anonymous",
            query={
                "position": position,
                "country": country,
                "city": city,
                "town": town,
                "working_preference": working_preference,
            },
            result_count=total,
        )
    )

    items = [JobPostingListItem.model_validate(j) for j in jobs]
    return PaginatedResponse.build(items=items, total=total, page=page, limit=limit)


async def get_recent_searches(user_id: str) -> list[dict]:
    db = get_mongodb()
    return await search_repository.get_recent_searches(db, user_id, limit=10)


async def autocomplete_positions(session: AsyncSession, prefix: str) -> list[str]:
    if not prefix or len(prefix) < 1:
        return []

    redis = get_redis()
    key = _AUTO_POS.format(prefix=prefix.lower())

    try:
        cached = await redis.get(key)
        if cached:
            import json
            return json.loads(cached)
    except Exception as exc:
        logger.warning("Redis get failed: %s", exc)

    results = await job_repository.autocomplete_positions(session, prefix, limit=10)

    try:
        import json
        await redis.set(key, json.dumps(results), ex=600)
    except Exception as exc:
        logger.warning("Redis set failed: %s", exc)

    return results


async def autocomplete_cities(session: AsyncSession, prefix: str) -> list[str]:
    if not prefix or len(prefix) < 1:
        return []

    redis = get_redis()
    key = _AUTO_CITY.format(prefix=prefix.lower())

    try:
        cached = await redis.get(key)
        if cached:
            import json
            return json.loads(cached)
    except Exception as exc:
        logger.warning("Redis get failed: %s", exc)

    results = await job_repository.autocomplete_cities(session, prefix, limit=10)

    try:
        import json
        await redis.set(key, json.dumps(results), ex=600)
    except Exception as exc:
        logger.warning("Redis set failed: %s", exc)

    return results


async def get_featured_jobs(session: AsyncSession, city: str) -> list[JobPostingListItem]:
    redis = get_redis()
    key = _FEATURED.format(city=city.lower())

    try:
        cached = await redis.get(key)
        if cached:
            import json
            data = json.loads(cached)
            return [JobPostingListItem.model_validate(item) for item in data]
    except Exception as exc:
        logger.warning("Redis get failed: %s", exc)

    jobs = await job_repository.get_by_city(session, city, limit=5)
    items = [JobPostingListItem.model_validate(j) for j in jobs]

    try:
        import json
        payload = [item.model_dump(mode="json") for item in items]
        await redis.set(key, json.dumps(payload, default=str), ex=300)
    except Exception as exc:
        logger.warning("Redis set failed: %s", exc)

    return items
