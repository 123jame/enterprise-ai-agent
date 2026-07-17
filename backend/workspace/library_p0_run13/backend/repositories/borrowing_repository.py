"""Borrowing record data access layer."""

from datetime import datetime, date
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.borrowing import Borrowing
from models.book import Book
from models.reader import Reader


class BorrowingRepository:
    """Repository handling Borrowing database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, borrowing: Borrowing) -> Borrowing:
        self.session.add(borrowing)
        await self.session.flush()
        return borrowing

    async def get_by_id(self, borrowing_id: int) -> Optional[Borrowing]:
        stmt = select(Borrowing).where(Borrowing.id == borrowing_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_borrowings_by_reader(self, reader_id: int) -> List[Borrowing]:
        """Get all currently borrowed (not returned) records for a reader."""
        stmt = (
            select(Borrowing)
            .where(
                and_(
                    Borrowing.reader_id == reader_id,
                    Borrowing.is_returned == False,  # noqa: E712
                )
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_borrowings_by_book(self, book_id: int) -> List[Borrowing]:
        """Get all currently borrowed records for a book."""
        stmt = (
            select(Borrowing)
            .where(
                and_(
                    Borrowing.book_id == book_id,
                    Borrowing.is_returned == False,  # noqa: E712
                )
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_active_by_reader(self, reader_id: int) -> int:
        """Count currently borrowed books for a reader."""
        stmt = (
            select(func.count())
            .select_from(Borrowing)
            .where(
                and_(
                    Borrowing.reader_id == reader_id,
                    Borrowing.is_returned == False,  # noqa: E712
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def has_overdue_by_reader(self, reader_id: int) -> bool:
        """Check if reader has any overdue books."""
        today = date.today()
        stmt = (
            select(func.count())
            .select_from(Borrowing)
            .where(
                and_(
                    Borrowing.reader_id == reader_id,
                    Borrowing.is_returned == False,  # noqa: E712
                    Borrowing.due_date < today,
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def update(self, borrowing: Borrowing) -> Borrowing:
        self.session.add(borrowing)
        await self.session.flush()
        return borrowing

    async def get_overdue_list(
        self, page: int = 1, page_size: int = 20
    ) -> Tuple[List, int]:
        """Get list of overdue borrowings with book and reader info."""
        today = date.today()
        query = (
            select(
                Borrowing.id,
                Book.title,
                Reader.name,
                Reader.id_card,
                Borrowing.borrow_date,
                Borrowing.due_date,
            )
            .join(Book, Borrowing.book_id == Book.id)
            .join(Reader, Borrowing.reader_id == Reader.id)
            .where(
                and_(
                    Borrowing.is_returned == False,  # noqa: E712
                    Borrowing.due_date < today,
                )
            )
            .order_by(Borrowing.due_date.asc())
        )

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.session.execute(query)
        rows = result.all()

        return rows, total

    async def get_popular_books(
        self, limit: int = 10
    ) -> List:
        """Get most borrowed books ranking."""
        query = (
            select(
                Book.id,
                Book.title,
                Book.author,
                func.count(Borrowing.id).label("borrow_count"),
            )
            .join(Borrowing, Borrowing.book_id == Book.id)
            .group_by(Book.id, Book.title, Book.author)
            .order_by(func.count(Borrowing.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.all()
