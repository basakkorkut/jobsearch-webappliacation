import logging
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.async_database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"ssl": "require", "statement_cache_size": 0},  # PgBouncer transaction mode requires this
    echo=settings.environment == "development",
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
