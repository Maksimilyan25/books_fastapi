from typing import Optional, List
from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID


class BookResponse(BaseModel):
    id: UUID
    title: str
    rating: Optional[Decimal] = None
    description: Optional[str] = None
    published_year: Optional[int] = None


class BooksListResponse(BaseModel):
    items: List[BookResponse]
    total: int
    page: int
    page_size: int


class BooksQueryParams(BaseModel):
    page: int = Field(
        ge=1, default=1, description='Номер страницы (начиная с 1)'
    )
    page_size: int = Field(
        ge=1, le=100, default=10, description='Размер страницы (от 1 до 100)'
    )
    sort: str = Field(
        default='title',
        description='Поле для сортировки: title|rating|published_year'
    )
    order: str = Field(
        default='asc', pattern='^(asc|desc)$',
        description='Порядок сортировки: asc|desc'
    )
    q: Optional[str] = Field(
        default=None, description='Поиск по подстроке в названии'
    )
    genre_id: Optional[UUID] = Field(
        default=None, description='Фильтр по жанру'
    )
    published_year: Optional[int] = Field(
        default=None, description='Фильтр по году публикации'
    )
    rating_min: Optional[Decimal] = Field(
        default=None, ge=0, le=99.9, description='Минимальный рейтинг'
    )
    rating_max: Optional[Decimal] = Field(
        default=None, ge=0, le=99.9, description='Максимальный рейтинг'
    )
