import math
from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int

    @classmethod
    def build(cls, items: list, total: int, page: int, limit: int) -> "PaginatedResponse":
        pages = math.ceil(total / limit) if limit > 0 else 0
        return cls(items=items, total=total, page=page, limit=limit, pages=pages)
