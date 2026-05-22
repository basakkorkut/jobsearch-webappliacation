"""
Alert Matcher — iş ilanını job_alerts tablosuyla eşleştirip MongoDB'ye notification yazar.

İki yerden çağrılır:
  1. RabbitMQ consumer (real-time): yeni ilan geldiğinde
  2. APScheduler Task 1 (safety net): son 1 saatte oluşan ilanları periyodik tarar
"""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.mongodb import get_mongodb
from app.models.job_alert import JobAlert
from app.models.job_posting import JobPosting

logger = logging.getLogger(__name__)


def _keywords_match(keywords: str, title: str, description: str) -> bool:
    """Her kelime başlık veya açıklamada geçiyor mu?"""
    text = f"{title} {description}".lower()
    return all(kw.strip().lower() in text for kw in keywords.split() if kw.strip())


async def match_and_notify(job_id: str, title: str, description: str,
                           city: str, country: str) -> int:
    """
    Verilen ilan için eşleşen alarmları bul ve bildirim yaz.
    Döndürür: oluşturulan bildirim sayısı
    """
    db: AsyncSession
    async with AsyncSessionLocal() as db:
        # Şehir veya ülkeyle eşleşen (ya da lokasyon filtresi olmayanlar) alarmları çek
        result = await db.execute(
            select(JobAlert).where(
                or_(
                    and_(JobAlert.city == None, JobAlert.country == None),
                    JobAlert.city == city,
                    JobAlert.country == country,
                )
            )
        )
        alerts = result.scalars().all()

    if not alerts:
        return 0

    mongo_db = get_mongodb()
    count = 0

    for alert in alerts:
        if not _keywords_match(alert.keywords, title, description):
            continue

        # Aynı user + job için duplicate bildirim engelle
        exists = await mongo_db.notifications.find_one({
            "user_id": str(alert.user_id),
            "job_posting_id": str(job_id),
        })
        if exists:
            continue

        await mongo_db.notifications.insert_one({
            "user_id":         str(alert.user_id),
            "job_posting_id":  str(job_id),
            "job_posting_title": title,
            "type":            "job_alert",
            "message":         f'"{alert.keywords}" aramanıza uyan yeni ilan: {title} — {city}',
            "read":            False,
            "created_at":      datetime.now(timezone.utc),
        })
        count += 1

    if count:
        logger.info("İlan %s → %d bildirim oluşturuldu", job_id, count)
    return count


async def scan_recent_jobs(since_minutes: int = 60) -> int:
    """APScheduler Task 1: son N dakikada oluşan ilanları tara."""
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(JobPosting).where(JobPosting.created_at >= cutoff)
        )
        jobs = result.scalars().all()

    total = 0
    for job in jobs:
        n = await match_and_notify(
            str(job.id), job.title, job.description, job.city, job.country
        )
        total += n

    logger.info("Periyodik tarama: %d ilan, %d yeni bildirim", len(jobs), total)
    return total


async def cleanup_old_notifications(days: int = 30) -> int:
    """APScheduler Task 2: N günden eski bildirimleri sil."""
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    mongo_db = get_mongodb()
    result = await mongo_db.notifications.delete_many({"created_at": {"$lt": cutoff}})
    deleted = result.deleted_count
    if deleted:
        logger.info("Temizlik: %d eski bildirim silindi (>%d gün)", deleted, days)
    return deleted
