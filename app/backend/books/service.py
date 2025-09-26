from typing import Optional
from uuid import UUID
from decimal import Decimal

from app.backend.database.db import SessionDep
from .repository import BookRepository
from .schemas import (
    BookResponse, BooksListResponse, BookCreate, BookUpdate,
    GenreResponse, ContributorResponse, BookContributorResponse,
    GenreCreate, GenreUpdate, GenresListResponse
)
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

        sort = sort_enum.value
        order = order_enum.value

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

        # Преобразуем модели в схемы ответа с полной информацией
        book_responses = []
        for book in books:
            # Получаем жанры книги
            genres = await self.repository.get_book_genres(book.id)
            genre_responses = [
                GenreResponse(id=genre.id, name=genre.name) for genre in genres
            ]

            # Получаем участников книги
            contributors_data = await self.repository.get_book_contributors(
                book.id
            )
            contributor_responses = [
                BookContributorResponse(
                    contributor=ContributorResponse(
                        id=contributor.id, full_name=contributor.full_name
                    ),
                    role=role
                )
                for contributor, role in contributors_data
            ]

            book_responses.append(BookResponse(
                id=book.id,
                title=book.title,
                rating=book.rating,
                description=book.description,
                published_year=book.published_year,
                genres=genre_responses,
                contributors=contributor_responses
            ))

        return BooksListResponse(
            items=book_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_book_by_id(self, book_id: UUID) -> Optional[BookResponse]:
        """
        Получить книгу по ID с информацией о жанрах и участниках.

        Args:
            book_id: ID книги

        Returns:
            Optional[BookResponse]: Данные книги или None, если не найдена
        """
        book = await self.repository.get_book_by_id(book_id)
        if not book:
            return None

        # Получаем жанры книги
        genres = await self.repository.get_book_genres(book_id)
        genre_responses = [
            GenreResponse(id=genre.id, name=genre.name) for genre in genres
        ]

        # Получаем участников книги
        contributors_data = await self.repository.get_book_contributors(
            book_id
        )
        contributor_responses = [
            BookContributorResponse(
                contributor=ContributorResponse(
                    id=contributor.id, full_name=contributor.full_name
                ),
                role=role
            )
            for contributor, role in contributors_data
        ]

        return BookResponse(
            id=book.id,
            title=book.title,
            rating=book.rating,
            description=book.description,
            published_year=book.published_year,
            genres=genre_responses,
            contributors=contributor_responses
        )

    async def create_book(self, book_data: BookCreate) -> BookResponse:
        """
        Создать новую книгу.

        Args:
            book_data: Данные для создания книги

        Returns:
            BookResponse: Созданная книга
        """
        # Создаем книгу
        book_dict = book_data.dict(exclude={"genre_ids", "contributors"})
        book = await self.repository.create_book(book_dict)

        # Добавляем жанры
        if book_data.genre_ids:
            await self.repository.update_book_genres(
                book.id, book_data.genre_ids
            )

        # Добавляем участников
        if book_data.contributors:
            contributors_data = [
                {"contributor_id": c.contributor_id, "role": c.role}
                for c in book_data.contributors
            ]
            await self.repository.update_book_contributors(
                book.id, contributors_data
            )

        return await self.get_book_by_id(book.id)

    async def update_book(
        self, book_id: UUID, book_data: BookUpdate
    ) -> Optional[BookResponse]:
        """
        Обновить существующую книгу.

        Args:
            book_id: ID книги
            book_data: Данные для обновления

        Returns:
            Optional[BookResponse]: Обновленная книга или None, если не найдена
        """
        # Обновляем основные данные книги
        update_dict = book_data.dict(
            exclude_unset=True, exclude={"genre_ids", "contributors"}
        )
        if update_dict:
            book = await self.repository.update_book(book_id, update_dict)
            if not book:
                return None

        # Обновляем жанры, если они указаны
        if book_data.genre_ids is not None:
            await self.repository.update_book_genres(
                book_id, book_data.genre_ids
            )

        # Обновляем участников, если они указаны
        if book_data.contributors is not None:
            contributors_data = [
                {"contributor_id": c.contributor_id, "role": c.role}
                for c in book_data.contributors
            ]
            await self.repository.update_book_contributors(
                book_id, contributors_data
            )

        return await self.get_book_by_id(book_id)

    async def delete_book(self, book_id: UUID) -> bool:
        """
        Удалить книгу.

        Args:
            book_id: ID книги

        Returns:
            bool: True если книга была удалена, False если не найдена
        """
        return await self.repository.delete_book(book_id)


class GenreService:
    """
    Сервис для работы с жанрами.

    Предоставляет бизнес-логику для операций с жанрами,
    включая получение списков жанров с фильтрацией и пагинацией.
    """

    def __init__(self, session: SessionDep):
        """
        Инициализация сервиса.

        Args:
            session: Сессия базы данных
        """
        self.repository = BookRepository(session)

    async def get_genres_list(
        self,
        page: int = 1,
        page_size: int = 10,
        q: Optional[str] = None,
    ) -> GenresListResponse:
        """
        Получить список жанров с фильтрацией и пагинацией.

        Args:
            page: Номер страницы (начиная с 1)
            page_size: Размер страницы (от 1 до 100)
            q: Поиск по подстроке в названии

        Returns:
            GenresListResponse: Список жанров с метаинформацией
        """
        # Валидация параметров
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 10

        genres, total = await self.repository.get_genres_list(
            page=page,
            page_size=page_size,
            q=q,
        )

        # Преобразуем модели в схемы ответа
        genre_responses = [
            GenreResponse(id=genre.id, name=genre.name) for genre in genres
        ]

        return GenresListResponse(
            items=genre_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_genre_by_id(self, genre_id: UUID) -> Optional[GenreResponse]:
        """
        Получить жанр по ID.

        Args:
            genre_id: ID жанра

        Returns:
            Optional[GenreResponse]: Данные жанра или None, если не найден
        """
        genre = await self.repository.get_genre_by_id(genre_id)
        if not genre:
            return None

        return GenreResponse(id=genre.id, name=genre.name)

    async def create_genre(self, genre_data: GenreCreate) -> GenreResponse:
        """
        Создать новый жанр.

        Args:
            genre_data: Данные для создания жанра

        Returns:
            GenreResponse: Созданный жанр

        Raises:
            ValueError: Если жанр с таким названием уже существует
        """
        # Проверяем, существует ли жанр с таким названием
        existing_genre = await self.repository.get_genre_by_name(
            genre_data.name
        )
        if existing_genre:
            raise ValueError(
                f"Жанр с названием '{genre_data.name}' уже существует"
            )

        genre_dict = genre_data.dict()
        genre = await self.repository.create_genre(genre_dict)

        return GenreResponse(id=genre.id, name=genre.name)

    async def update_genre(
        self, genre_id: UUID, genre_data: GenreUpdate
    ) -> Optional[GenreResponse]:
        """
        Обновить существующий жанр.

        Args:
            genre_id: ID жанра
            genre_data: Данные для обновления

        Returns:
            Optional[GenreResponse]: Обновленный жанр или None, если не найден

        Raises:
            ValueError: Если жанр с таким названием уже существует
        """
        # Если обновляется название, проверяем, не занято ли оно
        if genre_data.name:
            existing_genre = await self.repository.get_genre_by_name(
                genre_data.name
            )
            if existing_genre and existing_genre.id != genre_id:
                raise ValueError(
                    f"Жанр с названием '{genre_data.name}' уже существует"
                )

        update_dict = genre_data.dict(exclude_unset=True)
        if not update_dict:
            return await self.get_genre_by_id(genre_id)

        genre = await self.repository.update_genre(genre_id, update_dict)
        if not genre:
            return None

        return GenreResponse(id=genre.id, name=genre.name)

    async def delete_genre(self, genre_id: UUID) -> bool:
        """
        Удалить жанр.

        Args:
            genre_id: ID жанра

        Returns:
            bool: True если жанр был удален, False если не найден
        """
        return await self.repository.delete_genre(genre_id)
