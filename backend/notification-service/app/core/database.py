from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .config import settings


engine = create_async_engine(
    settings.async_database_url,
    pool_pre_ping=True,
    pool_size=3,
    max_overflow=5,
    connect_args={"ssl": "require", "statement_cache_size": 0},
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
