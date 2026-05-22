from datetime import datetime

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    job_posting_id: str
    job_posting_title: str
    message: str
    created_at: datetime
    read: bool
