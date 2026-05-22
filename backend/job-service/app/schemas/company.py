import uuid
from datetime import datetime

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    description: str | None = None
    logo_url: str | None = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    logo_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
