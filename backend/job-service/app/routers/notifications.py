from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.core.auth import CurrentUser, get_current_user
from app.core.mongodb import get_mongodb
from app.repositories import search_repository
from app.schemas.common import PaginatedResponse
from app.schemas.notification import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=PaginatedResponse)
async def list_notifications(
    read: bool | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
):
    db = get_mongodb()
    docs, total = await search_repository.get_notifications(db, current_user.id, read, page, limit)
    return PaginatedResponse.build(items=docs, total=total, page=page, limit=limit)


@router.patch("/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_read(
    notification_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    db = get_mongodb()
    updated = await search_repository.mark_notification_read(db, notification_id, current_user.id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"message": "Marked as read"}
