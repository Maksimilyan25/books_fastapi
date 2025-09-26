from typing import List, Optional, Tuple
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select, func, and_

from backend.database.db import SessionDep
from .models import Book, BookGenre, Genre, SortField, SortOrder


class BookRepository:
    """
    Репозиторий для работы с книгами в базе данных.

    Предоставляет методы для выполнения запросов к базе данных
    для получения информации о книгах.
    """

    def __init__(self, session: SessionDep):
        """
        Инициализация репозитория.

        Args:
            session: Сессия базы данных
        """

        self.session = session

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
    ) -> Tuple[List[Book], int]:

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
            Tuple[List[Book], int]: Кортеж из (список книг, общее количество)
        """

        query = select(Book)

        conditions = []

        if q:
            conditions.append(Book.title.ilike(f'%{q}%'))

        # Фильтр по жанру
        if genre_id:
            query = query.join(BookGenre, Book.id == BookGenre.book_id).join(
                Genre, BookGenre.genre_id == Genre.id
            )
            conditions.append(Genre.id == genre_id)

        # Фильтр по году публикации
        if published_year:
            conditions.append(Book.published_year == published_year)

        # Фильтр по диапазону рейтинга
        if rating_min is not None:
            conditions.append(Book.rating >= rating_min)

        if rating_max is not None:
            conditions.append(Book.rating <= rating_max)

        # Применяем все условия
        if conditions:
            query = query.where(and_(*conditions))

        # Получаем общее количество записей
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        # Применяем сортировку
        try:
            sort_enum = SortField(sort)
        except ValueError:
            sort_enum = SortField.TITLE

        try:
            order_enum = SortOrder(order)
        except ValueError:
            order_enum = SortOrder.ASC

        # Определяем колонку для сортировки
        if sort_enum == SortField.TITLE:
            sort_column = Book.title
        elif sort_enum == SortField.RATING:
            sort_column = Book.rating
        elif sort_enum == SortField.PUBLISHED_YEAR:
            sort_column = Book.published_year
        else:
            sort_column = Book.title

        # Применяем порядок сортировки
        if order_enum == SortOrder.DESC:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Применяем пагинацию
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        books = result.scalars().all()

        return list(books), total or 0
