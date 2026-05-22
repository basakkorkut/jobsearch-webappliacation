import certifi
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


async def connect_mongodb() -> None:
    global _client
    _client = AsyncIOMotorClient(settings.mongodb_uri, tlsCAFile=certifi.where())
    db: AsyncIOMotorDatabase = _client[settings.mongodb_db_name]

    await db.job_searches.create_index([("user_id", 1), ("timestamp", -1)])
    await db.job_searches.create_index([("timestamp", -1)])
    await db.notifications.create_index(
        [("user_id", 1), ("read", 1), ("created_at", -1)]
    )
    logger.info("MongoDB connected, indexes ensured")


async def disconnect_mongodb() -> None:
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("MongoDB disconnected")


def get_mongodb() -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("MongoDB client not initialised")
    return _client[settings.mongodb_db_name]


def get_client() -> AsyncIOMotorClient:
    if _client is None:
        raise RuntimeError("MongoDB client not initialised")
    return _client
