import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_profile import UserProfile


async def get_role(session: AsyncSession, user_id: uuid.UUID) -> Optional[str]:
    result = await session.execute(
        select(UserProfile.role).where(UserProfile.id == user_id)
    )
    return result.scalar_one_or_none()
