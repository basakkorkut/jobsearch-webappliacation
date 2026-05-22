import uuid
from datetime import datetime

from pydantic import BaseModel


class JobAlertCreate(BaseModel):
    keywords: str
    country: str | None = None
    city: str | None = None
    town: str | None = None


class JobAlertResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    keywords: str
    country: str | None = None
    city: str | None = None
    town: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
