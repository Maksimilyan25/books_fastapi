from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Query

from backend.database.db import SessionDep
from .schemas import BooksListResponse
from .service import BookService

router = APIRouter(prefix='/books')


@router.get('/', response_model=BooksListResponse)
async def get_books(
    session: SessionDep,
    page: int = Query(
        ge=1, default=1, description='Номер страницы (начиная с 1)'
    ),
    page_size: int = Query(
        ge=1, le=100, default=10, description='Размер страницы (от 1 до 100)'
    ),
    sort: str = Query(
        default='title',
        description='Поле для сортировки: title|rating|published_year'
    ),
    order: str = Query(
        default='asc', regex='^(asc|desc)$',
        description='Порядок сортировки: asc|desc'
    ),
    q: str = Query(
        default=None, description='Поиск по подстроке в названии'
    ),
    genre_id: UUID = Query(
        default=None, description='Фильтр по жанру'
    ),
    published_year: int = Query(
        default=None, description='Фильтр по году публикации'
    ),
    rating_min: Decimal = Query(
        default=None, ge=0, le=99.9, description='Минимальный рейтинг'
    ),
    rating_max: Decimal = Query(
        default=None, ge=0, le=99.9, description='Максимальный рейтинг'
    ),
):
    """
    Получить список книг с фильтрацией, сортировкой и пагинацией.

    Args:
        session: Сессия базы данных
        page: Номер страницы (начиная с 1)
        page_size: Размер страницы (от 1 до 100)
        sort: Поле для сортировки (title|rating|published_year)
        order: Порядок сортировки (asc|desc)
        q: Поиск по подстроке в названии
        genre_id: Фильтр по жанру
        published_year: Фильтр по году публикации
        rating_min: Минимальный рейтинг
        rating_max: Максимальный рейтинг

    Returns:
        BooksListResponse: Список книг с метаинформацией
    """
    service = BookService(session)
    return await service.get_books_list(
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
        q=q,
        genre_id=genre_id,
        published_year=published_year,
        rating_min=rating_min,
        rating_max=rating_max,
    )
