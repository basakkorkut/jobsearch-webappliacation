import uuid
from datetime import datetime

from pydantic import BaseModel


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_posting_id: uuid.UUID
    applied_at: datetime

    model_config = {"from_attributes": True}
