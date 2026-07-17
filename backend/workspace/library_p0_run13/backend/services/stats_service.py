"""Statistics business logic layer."""

from typing import List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.book import Book
from models.reader import Reader
from models.borrowing import Borrowing
from schemas.stats import (
    BookStatsResponse,
    ReaderStatsResponse,
    PopularBookResponse,
    OverdueBorrowingResponse,
)
from repositories.borrowing_repository import BorrowingRepository


class StatsService:
    """Service for gathering statistics."""

    def __init__(self, session: AsyncSession, borrowing_repo: BorrowingRepository):
        self.session = session
        self.borrowing_repo = borrowing_repo

    async def get_book_stats(self) -> BookStatsResponse:
        """Get book statistics: total, categories, borrowed count."""
        # Total active books
        total_result = await self.session.execute(
            select(func.count()).select_from(Book).where(Book.is_active == True)  # noqa: E712
        )
        total_books = total_result.scalar_one()

        # Category distribution
        cat_result = await self.session.execute(
            select(Book.category, func.count(Book.id).label("count"))
            .where(Book.is_active == True)  # noqa: E712
            .group_by(Book.category)
        )
        category_distribution = [
            {"category": row.category, "count": row.count}
            for row in cat_result.all()
        ]

        total_categories = len(category_distribution)

        # Currently borrowed
        borrowed_result = await self.session.execute(
            select(func.count())
            .select_from(Borrowing)
            .where(Borrowing.is_returned == False)  # noqa: E712
        )
        currently_borrowed = borrowed_result.scalar_one()

        return BookStatsResponse(
            total_books=total_books,
            total_categories=total_categories,
            category_distribution=category_distribution,
            currently_borrowed=currently_borrowed,
        )

    async def get_reader_stats(self) -> ReaderStatsResponse:
        """Get reader statistics: total and active."""
        total_result = await self.session.execute(
            select(func.count()).select_from(Reader)
        )
        total_readers = total_result.scalar_one()

        # Active readers = those with current borrowings
        active_result = await self.session.execute(
            select(func.count(func.distinct(Borrowing.reader_id)))
            .where(Borrowing.is_returned == False)  # noqa: E712
        )
        active_readers = active_result.scalar_one()

        return ReaderStatsResponse(
            total_readers=total_readers,
            active_readers=active_readers,
        )

    async def get_popular_books(self, limit: int = 10) -> List[PopularBookResponse]:
        """Get most borrowed books."""
        rows = await self.borrowing_repo.get_popular_books(limit=limit)
        return [
            PopularBookResponse(
                book_id=row.id,
                title=row.title,
                author=row.author,
                borrow_count=row.borrow_count,
            )
            for row in rows
        ]

    async def get_overdue_borrowings(
        self, page: int = 1, page_size: int = 20
    ) -> dict:
        """Get overdue borrowing list."""
        rows, total = await self.borrowing_repo.get_overdue_list(
            page=page, page_size=page_size
        )
        from datetime import date

        today = date.today()
        items = []
        for row in rows:
            overdue_days = (today - row.due_date).days
            items.append(
                OverdueBorrowingResponse(
                    borrowing_id=row.id,
                    book_title=row.title,
                    reader_name=row.name,
                    reader_id_card=row.id_card,
                    borrow_date=str(row.borrow_date.date()),
                    due_date=str(row.due_date),
                    overdue_days=overdue_days,
                )
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
