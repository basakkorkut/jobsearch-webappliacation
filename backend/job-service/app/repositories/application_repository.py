import uuid

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application


async def apply(session: AsyncSession, user_id: uuid.UUID, job_posting_id: uuid.UUID) -> Application:
    app_obj = Application(user_id=user_id, job_posting_id=job_posting_id)
    session.add(app_obj)
    try:
        await session.flush()
        await session.execute(
            text("SELECT increment_application_count(:job_id)"),
            {"job_id": str(job_posting_id)},
        )
        await session.commit()
        return app_obj
    except IntegrityError:
        await session.rollback()
        raise
