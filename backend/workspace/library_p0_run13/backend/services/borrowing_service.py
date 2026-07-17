"""Borrowing business logic layer."""

from datetime import date, timedelta, datetime
from typing import List
from fastapi import HTTPException, status

from config import settings
from models.borrowing import Borrowing
from models.book import Book
from models.reader import Reader
from schemas.borrowing import BorrowRequest, ReturnRequest, ActiveBorrowingResponse
from repositories.borrowing_repository import BorrowingRepository
from repositories.book_repository import BookRepository
from repositories.reader_repository import ReaderRepository


class BorrowingService:
    """Service handling borrowing and returning business rules."""

    def __init__(
        self,
        borrowing_repo: BorrowingRepository,
        book_repo: BookRepository,
        reader_repo: ReaderRepository,
    ):
        self.borrowing_repo = borrowing_repo
        self.book_repo = book_repo
        self.reader_repo = reader_repo

    async def borrow_book(self, data: BorrowRequest) -> Borrowing:
        """Borrow a book for a reader with business rule validation."""
        # 1. Validate book exists and is available
        book = await self.book_repo.get_by_id(data.book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在"
            )
        if not book.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="图书已下架，无法借阅"
            )
        if book.available_stock < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="图书库存不足"
            )

        # 2. Validate reader exists and is active
        reader = await self.reader_repo.get_by_id(data.reader_id)
        if not reader:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="读者不存在"
            )
        if not reader.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="读者账号已被冻结"
            )

        # 3. Check borrowing limit (max 5 active borrows)
        active_count = await self.borrowing_repo.count_active_by_reader(data.reader_id)
        if active_count >= settings.MAX_BORROW_BOOKS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"读者已借阅 {active_count} 册，达到上限 {settings.MAX_BORROW_BOOKS} 册",
            )

        # 4. Check overdue books
        has_overdue = await self.borrowing_repo.has_overdue_by_reader(data.reader_id)
        if has_overdue:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="读者存在逾期未还图书，请先归还后再借阅",
            )

        # 5. Create borrowing record
        due_date = date.today() + timedelta(days=settings.DEFAULT_BORROW_DAYS)
        borrowing = Borrowing(
            book_id=data.book_id,
            reader_id=data.reader_id,
            due_date=due_date,
            is_returned=False,
        )
        borrowing = await self.borrowing_repo.create(borrowing)

        # 6. Decrease available stock
        book.available_stock -= 1
        await self.book_repo.update(book)

        return borrowing

    async def return_book(self, data: ReturnRequest) -> Borrowing:
        """Return a borrowed book."""
        borrowing = await self.borrowing_repo.get_by_id(data.borrowing_id)
        if not borrowing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="借阅记录不存在"
            )
        if borrowing.is_returned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="该书已归还"
            )

        # Update borrowing record
        borrowing.is_returned = True
        borrowing.return_date = datetime.now()
        borrowing = await self.borrowing_repo.update(borrowing)

        # Increase available stock
        book = await self.book_repo.get_by_id(borrowing.book_id)
        if book:
            book.available_stock += 1
            await self.book_repo.update(book)

        return borrowing

    async def get_active_borrowings_by_reader(
        self, reader_id: int
    ) -> List[ActiveBorrowingResponse]:
        """Get all active (not returned) borrowings for a reader with overdue info."""
        borrowings = await self.borrowing_repo.get_active_borrowings_by_reader(
            reader_id
        )
        today = date.today()
        result = []
        for b in borrowings:
            book = await self.book_repo.get_by_id(b.book_id)
            reader = await self.reader_repo.get_by_id(b.reader_id)
            is_overdue = b.due_date < today
            overdue_days = (today - b.due_date).days if is_overdue else 0
            result.append(
                ActiveBorrowingResponse(
                    id=b.id,
                    book_id=b.book_id,
                    book_title=book.title if book else "未知",
                    reader_id=b.reader_id,
                    reader_name=reader.name if reader else "未知",
                    borrow_date=b.borrow_date,
                    due_date=b.due_date,
                    is_overdue=is_overdue,
                    overdue_days=overdue_days,
                )
            )
        return result
