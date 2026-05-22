import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company


async def get_by_id(session: AsyncSession, company_id: uuid.UUID) -> Optional[Company]:
    result = await session.execute(select(Company).where(Company.id == company_id))
    return result.scalar_one_or_none()


async def list_companies(session: AsyncSession, page: int, limit: int) -> tuple[list[Company], int]:
    total: int = await session.scalar(select(func.count(Company.id))) or 0
    rows = await session.execute(
        select(Company).order_by(Company.name).offset((page - 1) * limit).limit(limit)
    )
    return list(rows.scalars().all()), total


async def create_company(session: AsyncSession, **data) -> Company:
    company = Company(**data)
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company
