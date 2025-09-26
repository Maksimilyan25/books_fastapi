from typing import List, Optional, Tuple
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select, func, and_, delete

from app.backend.database.db import SessionDep
from .models import (
    Book,
    BookGenre,
    Genre,
    Contributor,
    BookContributor,
    SortField,
    SortOrder,
    Role,
)


class BookRepository:
    def __init__(self, session: SessionDep):
        self.session = session

    async def get_books_list(
        self,
        page: int = 1,
        page_size: int = 10,
        sort: str = "title",
        order: str = "asc",
        q: Optional[str] = None,
        genre_id: Optional[UUID] = None,
        published_year: Optional[int] = None,
        rating_min: Optional[Decimal] = None,
        rating_max: Optional[Decimal] = None,
    ) -> Tuple[List[Book], int]:
        query = select(Book)
        conditions = []

        if q:
            conditions.append(Book.title.ilike(f"%{q}%"))

        if genre_id:
            query = query.join(BookGenre, Book.id == BookGenre.book_id).join(
                Genre, BookGenre.genre_id == Genre.id
            )
            conditions.append(Genre.id == genre_id)

        if published_year:
            conditions.append(Book.published_year == published_year)

        if rating_min is not None:
            conditions.append(Book.rating >= rating_min)

        if rating_max is not None:
            conditions.append(Book.rating <= rating_max)

        if conditions:
            query = query.where(and_(*conditions))

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        try:
            sort_enum = SortField(sort)
        except ValueError:
            sort_enum = SortField.TITLE

        try:
            order_enum = SortOrder(order)
        except ValueError:
            order_enum = SortOrder.ASC

        if sort_enum == SortField.TITLE:
            sort_column = Book.title
        elif sort_enum == SortField.RATING:
            sort_column = Book.rating
        elif sort_enum == SortField.PUBLISHED_YEAR:
            sort_column = Book.published_year
        else:
            sort_column = Book.title

        if order_enum == SortOrder.DESC:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        books = result.scalars().all()

        return list(books), total or 0

    async def get_book_by_id(self, book_id: UUID) -> Optional[Book]:
        query = select(Book).where(Book.id == book_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_book_genres(self, book_id: UUID) -> List[Genre]:
        query = select(Genre).join(BookGenre).where(
            BookGenre.book_id == book_id
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_book_contributors(
        self, book_id: UUID
    ) -> List[Tuple[Contributor, Role]]:
        query = (
            select(Contributor, BookContributor.role)
            .join(
                BookContributor,
                Contributor.id == BookContributor.contributor_id
            )
            .where(BookContributor.book_id == book_id)
        )
        result = await self.session.execute(query)
        return list(result.all())

    async def create_book(self, book_data: dict) -> Book:
        book = Book(**book_data)
        self.session.add(book)
        await self.session.flush()
        await self.session.refresh(book)
        return book

    async def update_book(
        self, book_id: UUID, book_data: dict
    ) -> Optional[Book]:
        query = select(Book).where(Book.id == book_id)
        result = await self.session.execute(query)
        book = result.scalar_one_or_none()
        if not book:
            return None

        for key, value in book_data.items():
            if hasattr(book, key) and value is not None:
                setattr(book, key, value)

        await self.session.flush()
        await self.session.refresh(book)
        return book

    async def delete_book(self, book_id: UUID) -> bool:
        query = select(Book).where(Book.id == book_id)
        result = await self.session.execute(query)
        book = result.scalar_one_or_none()

        if not book:
            return False

        await self.session.delete(book)
        await self.session.flush()
        return True

    async def update_book_genres(
        self, book_id: UUID, genre_ids: List[UUID]
    ) -> None:
        await self.session.execute(
            delete(BookGenre).where(BookGenre.book_id == book_id)
        )
        for genre_id in genre_ids:
            book_genre = BookGenre(book_id=book_id, genre_id=genre_id)
            self.session.add(book_genre)

        await self.session.flush()

    async def update_book_contributors(
        self, book_id: UUID, contributors_data: List[dict]
    ) -> None:
        await self.session.execute(
            delete(BookContributor).where(BookContributor.book_id == book_id)
        )
        for contributor_data in contributors_data:
            book_contributor = BookContributor(
                book_id=book_id,
                contributor_id=contributor_data["contributor_id"],
                role=contributor_data["role"],
            )
            self.session.add(book_contributor)

        await self.session.flush()

    # Методы для работы с жанрами
    async def get_genres_list(
        self,
        page: int = 1,
        page_size: int = 10,
        q: Optional[str] = None,
    ) -> Tuple[List[Genre], int]:
        query = select(Genre)
        conditions = []

        if q:
            conditions.append(Genre.name.ilike(f"%{q}%"))

        if conditions:
            query = query.where(and_(*conditions))

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        offset = (page - 1) * page_size
        query = query.order_by(Genre.name.asc()).offset(offset).limit(
            page_size
        )

        result = await self.session.execute(query)
        genres = result.scalars().all()

        return list(genres), total or 0

    async def get_genre_by_id(self, genre_id: UUID) -> Optional[Genre]:
        query = select(Genre).where(Genre.id == genre_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_genre_by_name(self, name: str) -> Optional[Genre]:
        query = select(Genre).where(Genre.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_genre(self, genre_data: dict) -> Genre:
        genre = Genre(**genre_data)
        self.session.add(genre)
        await self.session.flush()
        await self.session.refresh(genre)
        return genre

    async def update_genre(
        self, genre_id: UUID, genre_data: dict
    ) -> Optional[Genre]:
        query = select(Genre).where(Genre.id == genre_id)
        result = await self.session.execute(query)
        genre = result.scalar_one_or_none()
        if not genre:
            return None

        for key, value in genre_data.items():
            if hasattr(genre, key) and value is not None:
                setattr(genre, key, value)

        await self.session.flush()
        await self.session.refresh(genre)
        return genre

    async def delete_genre(self, genre_id: UUID) -> bool:
        query = select(Genre).where(Genre.id == genre_id)
        result = await self.session.execute(query)
        genre = result.scalar_one_or_none()

        if not genre:
            return False

        await self.session.delete(genre)
        await self.session.flush()
        return True
