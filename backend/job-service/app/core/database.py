import logging
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings

logger = logging.getLogger(__name__)

# psycopg3 (asyncpg yerine) — PgBouncer transaction mode ile tam uyumlu.
# prepare_threshold=None: prepared statement hiç kullanılmaz.
_db_url = settings.async_database_url.replace(
    "postgresql+asyncpg://", "postgresql+psycopg://"
).replace(
    "postgresql://", "postgresql+psycopg://"
)

engine = create_async_engine(
    _db_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "sslmode": "require",
        "prepare_threshold": None,
    },
    echo=False,
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
