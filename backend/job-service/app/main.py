import certifi
import os

# macOS Python SSL fix: point all SSL clients to certifi's CA bundle
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core import mongodb, rabbitmq
from app.core.config import settings
from app.core.database import AsyncSessionFactory
from app.core.redis_client import get_redis

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Job Service starting up…")

    try:
        await mongodb.connect_mongodb()
    except Exception as exc:
        logger.error("MongoDB startup error: %s", exc)

    try:
        await rabbitmq.connect_rabbitmq()
    except Exception as exc:
        logger.error("RabbitMQ startup error: %s", exc)

    logger.info("Job Service ready")
    yield

    logger.info("Job Service shutting down…")
    await mongodb.disconnect_mongodb()
    await rabbitmq.disconnect_rabbitmq()


app = FastAPI(
    title="Job Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from app.routers import jobs, search, alerts, companies, notifications

app.include_router(jobs.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    services: dict[str, str] = {}

    # PostgreSQL
    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        services["postgres"] = "up"
    except Exception as exc:
        logger.warning("Postgres health check failed: %s", exc)
        services["postgres"] = "down"

    # MongoDB
    try:
        db = mongodb.get_mongodb()
        await db.command("ping")
        services["mongodb"] = "up"
    except Exception as exc:
        logger.warning("MongoDB health check failed: %s", exc)
        services["mongodb"] = "down"

    # Redis (Upstash)
    try:
        redis = get_redis()
        await redis.ping()
        services["redis"] = "up"
    except Exception as exc:
        logger.warning("Redis health check failed: %s", exc)
        services["redis"] = "down"

    # RabbitMQ
    try:
        conn = rabbitmq._connection
        services["rabbitmq"] = "up" if (conn and not conn.is_closed) else "down"
    except Exception:
        services["rabbitmq"] = "down"

    overall = "ok" if all(v == "up" for v in services.values()) else "degraded"
    return {"status": overall, "services": services}
