import certifi
import logging
import os

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from app.core.config import settings
from app.core.database import engine
from app.core.mongodb import connect_mongodb, disconnect_mongodb
from app.core.rabbitmq import connect_rabbitmq, disconnect_rabbitmq
from app.services.alert_matcher import (
    match_and_notify,
    scan_recent_jobs,
    cleanup_old_notifications,
)

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def on_new_job(payload: dict) -> None:
    """RabbitMQ'dan gelen job.created event'ini işle."""
    await match_and_notify(
        job_id=payload.get("job_posting_id", ""),
        title=payload.get("title", ""),
        description=payload.get("description", ""),
        city=payload.get("city", ""),
        country=payload.get("country", ""),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Notification Service başlatılıyor...")

    # MongoDB
    await connect_mongodb()

    # RabbitMQ consumer
    await connect_rabbitmq(on_new_job)

    # APScheduler
    # Task 1: her 5 dakikada bir son 1 saatteki ilanları tara (kaçıranlar için)
    scheduler.add_job(scan_recent_jobs, "interval", minutes=5, id="scan_recent")
    # Task 2: her gece 02:00'de 30 günden eski bildirimleri temizle
    scheduler.add_job(cleanup_old_notifications, "cron", hour=2, minute=0, id="cleanup")
    scheduler.start()
    logger.info("APScheduler başlatıldı (2 task)")

    logger.info("Notification Service hazır")
    yield

    scheduler.shutdown(wait=False)
    await disconnect_rabbitmq()
    await disconnect_mongodb()
    await engine.dispose()
    logger.info("Notification Service kapatıldı")


app = FastAPI(title="Notification Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    from app.core.mongodb import get_mongodb
    mongo_ok = "down"
    try:
        await get_mongodb().command("ping")
        mongo_ok = "up"
    except Exception:
        pass

    scheduler_ok = "up" if scheduler.running else "down"

    return {
        "status": "ok",
        "services": {
            "mongodb":   mongo_ok,
            "scheduler": scheduler_ok,
        },
    }
