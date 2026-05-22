import uuid
from datetime import datetime

from sqlalchemy import Text, Integer, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id:          Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    title:       Mapped[str]       = mapped_column(Text, nullable=False)
    description: Mapped[str]       = mapped_column(Text, nullable=False)
    country:     Mapped[str]       = mapped_column(Text, nullable=False)
    city:        Mapped[str]       = mapped_column(Text, nullable=False)
    town:        Mapped[str | None] = mapped_column(Text, nullable=True)
    working_preference: Mapped[str | None] = mapped_column(Text, nullable=True)
    position_level:     Mapped[str | None] = mapped_column(Text, nullable=True)
    department:         Mapped[str | None] = mapped_column(Text, nullable=True)
    employment_type:    Mapped[str | None] = mapped_column(Text, nullable=True)
    application_count:  Mapped[int]        = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
