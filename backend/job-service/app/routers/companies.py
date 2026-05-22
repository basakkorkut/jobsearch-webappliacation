import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.repositories import company_repository, user_profile_repository
from app.schemas.company import CompanyCreate, CompanyResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=PaginatedResponse)
async def list_companies(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    companies, total = await company_repository.list_companies(db, page, limit)
    items = [CompanyResponse.model_validate(c) for c in companies]
    return PaginatedResponse.build(items=items, total=total, page=page, limit=limit)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    company = await company_repository.get_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return CompanyResponse.model_validate(company)


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    body: CompanyCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    role = await user_profile_repository.get_role(db, uuid.UUID(current_user.id))
    if role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    company = await company_repository.create_company(db, **body.model_dump())
    return CompanyResponse.model_validate(company)
