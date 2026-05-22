import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from .company import CompanyResponse

WorkingPreference = Literal["remote", "on_site", "hybrid"]
PositionLevel = Literal["junior", "mid", "senior", "expert", "intern"]
EmploymentType = Literal["full_time", "part_time", "contract", "internship"]


class JobPostingCreate(BaseModel):
    company_id: uuid.UUID
    title: str
    description: str
    country: str
    city: str
    town: str | None = None
    working_preference: WorkingPreference | None = None
    position_level: PositionLevel | None = None
    department: str | None = None
    employment_type: EmploymentType | None = None


class JobPostingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    country: str | None = None
    city: str | None = None
    town: str | None = None
    working_preference: WorkingPreference | None = None
    position_level: PositionLevel | None = None
    department: str | None = None
    employment_type: EmploymentType | None = None


class JobPostingResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company: CompanyResponse | None = None
    title: str
    description: str
    country: str
    city: str
    town: str | None = None
    working_preference: str | None = None
    position_level: str | None = None
    department: str | None = None
    employment_type: str | None = None
    application_count: int
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobPostingListItem(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company: CompanyResponse | None = None
    title: str
    country: str
    city: str
    town: str | None = None
    working_preference: str | None = None
    position_level: str | None = None
    department: str | None = None
    employment_type: str | None = None
    application_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
