from typing import Generic, Optional, TypeVar, List

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: Optional[T] = None


class PageData(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
