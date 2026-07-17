"""Book data access layer."""

from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.book import Book


class BookRepository:
    """Repository handling Book database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, book: Book) -> Book:
        self.session.add(book)
        await self.session.flush()
        return book

    async def get_by_id(self, book_id: int) -> Optional[Book]:
        stmt = select(Book).where(Book.id == book_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_isbn(self, isbn: str) -> Optional[Book]:
        stmt = select(Book).where(Book.isbn == isbn)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Book], int]:
        """Search books with filters and pagination. Returns (books, total_count)."""
        query = select(Book)

        # Apply filters
        if keyword:
            like_pattern = f"%{keyword}%"
            query = query.where(
                or_(
                    Book.title.ilike(like_pattern),
                    Book.author.ilike(like_pattern),
                    Book.isbn.ilike(like_pattern),
                )
            )
        if category:
            query = query.where(Book.category == category)
        if is_active is not None:
            query = query.where(Book.is_active == is_active)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Paginate
        offset = (page - 1) * page_size
        query = query.order_by(Book.id.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(query)
        books = list(result.scalars().all())

        return books, total

    async def update(self, book: Book) -> Book:
        self.session.add(book)
        await self.session.flush()
        return book

    async def delete(self, book: Book) -> None:
        await self.session.delete(book)
        await self.session.flush()
