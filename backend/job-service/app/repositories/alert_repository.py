import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_alert import JobAlert


async def get_by_id(session: AsyncSession, alert_id: uuid.UUID) -> Optional[JobAlert]:
    result = await session.execute(select(JobAlert).where(JobAlert.id == alert_id))
    return result.scalar_one_or_none()


async def list_by_user(session: AsyncSession, user_id: uuid.UUID) -> list[JobAlert]:
    rows = await session.execute(
        select(JobAlert).where(JobAlert.user_id == user_id).order_by(JobAlert.created_at.desc())
    )
    return list(rows.scalars().all())


async def create_alert(session: AsyncSession, **data) -> JobAlert:
    alert = JobAlert(**data)
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


async def delete_alert(session: AsyncSession, alert: JobAlert) -> None:
    await session.delete(alert)
    await session.commit()
