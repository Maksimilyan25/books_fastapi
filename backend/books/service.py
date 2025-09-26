from typing import Optional
from uuid import UUID
from decimal import Decimal

from backend.database.db import SessionDep
from .repository import BookRepository
from .schemas import BookResponse, BooksListResponse
from .models import SortField, SortOrder


class BookService:
    """
    Сервис для работы с книгами.

    Предоставляет бизнес-логику для операций с книгами,
    включая получение списков книг с фильтрацией, сортировкой и пагинацией.
    """

    def __init__(self, session: SessionDep):
        """
        Инициализация сервиса.

        Args:
            session: Сессия базы данных
        """
        self.repository = BookRepository(session)

    async def get_books_list(
        self,
        page: int = 1,
        page_size: int = 10,
        sort: str = 'title',
        order: str = 'asc',
        q: Optional[str] = None,
        genre_id: Optional[UUID] = None,
        published_year: Optional[int] = None,
        rating_min: Optional[Decimal] = None,
        rating_max: Optional[Decimal] = None,
    ) -> BooksListResponse:
        """
        Получить список книг с фильтрацией, сортировкой и пагинацией.

        Args:
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
        # Валидация параметров
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 10

        # Преобразуем строки в Enum
        try:
            sort_enum = SortField(sort)
        except ValueError:
            sort_enum = SortField.TITLE

        try:
            order_enum = SortOrder(order)
        except ValueError:
            order_enum = SortOrder.ASC

        # Преобразуем Enum обратно в строки для совместимости
        sort = sort_enum.value
        order = order_enum.value

        # Получаем данные из репозитория
        books, total = await self.repository.get_books_list(
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

        # Преобразуем модели в схемы ответа
        book_responses = [
            BookResponse(
                id=book.id,
                title=book.title,
                rating=book.rating,
                description=book.description,
                published_year=book.published_year,
            )
            for book in books
        ]

        return BooksListResponse(
            items=book_responses,
            total=total,
            page=page,
            page_size=page_size,
        )
