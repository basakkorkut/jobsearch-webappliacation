from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def log_search(
    db: AsyncIOMotorDatabase,
    user_id: str,
    query: dict,
    result_count: int,
) -> None:
    await db.job_searches.insert_one({
        "user_id": user_id,
        "query": query,
        "timestamp": datetime.now(timezone.utc),
        "result_count": result_count,
    })


async def get_recent_searches(
    db: AsyncIOMotorDatabase,
    user_id: str,
    limit: int = 10,
) -> list[dict]:
    cursor = db.job_searches.find(
        {"user_id": user_id},
        sort=[("timestamp", -1)],
        limit=limit,
    )
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["id"] = str(doc.pop("_id"))
        if isinstance(doc.get("timestamp"), datetime):
            doc["timestamp"] = doc["timestamp"].isoformat()
    return docs


async def get_notifications(
    db: AsyncIOMotorDatabase,
    user_id: str,
    read: Optional[bool],
    page: int,
    limit: int,
) -> tuple[list[dict], int]:
    filter_q: dict = {"user_id": user_id}
    if read is not None:
        filter_q["read"] = read

    total = await db.notifications.count_documents(filter_q)
    cursor = db.notifications.find(
        filter_q,
        sort=[("created_at", -1)],
        skip=(page - 1) * limit,
        limit=limit,
    )
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["id"] = str(doc.pop("_id"))
        if isinstance(doc.get("created_at"), datetime):
            doc["created_at"] = doc["created_at"].isoformat()
    return docs, total


async def mark_notification_read(
    db: AsyncIOMotorDatabase,
    notification_id: str,
    user_id: str,
) -> bool:
    result = await db.notifications.update_one(
        {"_id": ObjectId(notification_id), "user_id": user_id},
        {"$set": {"read": True}},
    )
    return result.modified_count > 0
