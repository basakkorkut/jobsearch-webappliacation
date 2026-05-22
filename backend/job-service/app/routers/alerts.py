import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.repositories import alert_repository
from app.schemas.job_alert import JobAlertCreate, JobAlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[JobAlertResponse])
async def list_alerts(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alerts = await alert_repository.list_by_user(db, uuid.UUID(current_user.id))
    return [JobAlertResponse.model_validate(a) for a in alerts]


@router.post("", response_model=JobAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    body: JobAlertCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alert = await alert_repository.create_alert(
        db,
        user_id=uuid.UUID(current_user.id),
        keywords=body.keywords,
        country=body.country,
        city=body.city,
        town=body.town,
    )
    return JobAlertResponse.model_validate(alert)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alert = await alert_repository.get_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert.user_id != uuid.UUID(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your alert")
    await alert_repository.delete_alert(db, alert)
