"""Borrowing API endpoints."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from repositories.borrowing_repository import BorrowingRepository
from repositories.book_repository import BookRepository
from repositories.reader_repository import ReaderRepository
from services.borrowing_service import BorrowingService
from schemas.borrowing import (
    BorrowRequest,
    ReturnRequest,
    BorrowingResponse,
    ActiveBorrowingResponse,
)

router = APIRouter(prefix="/api/borrowings", tags=["图书借阅与归还"])


async def get_borrowing_service(
    db: AsyncSession = Depends(get_db),
) -> BorrowingService:
    borrowing_repo = BorrowingRepository(db)
    book_repo = BookRepository(db)
    reader_repo = ReaderRepository(db)
    return BorrowingService(borrowing_repo, book_repo, reader_repo)


@router.post("/borrow", response_model=BorrowingResponse, status_code=201)
async def borrow_book(
    data: BorrowRequest,
    service: BorrowingService = Depends(get_borrowing_service),
):
    """借书操作（管理员）"""
    borrowing = await service.borrow_book(data)
    return BorrowingResponse.model_validate(borrowing)


@router.post("/return", response_model=BorrowingResponse)
async def return_book(
    data: ReturnRequest,
    service: BorrowingService = Depends(get_borrowing_service),
):
    """还书操作（管理员）"""
    borrowing = await service.return_book(data)
    return BorrowingResponse.model_validate(borrowing)


@router.get("/reader/{reader_id}", response_model=List[ActiveBorrowingResponse])
async def get_reader_active_borrowings(
    reader_id: int,
    service: BorrowingService = Depends(get_borrowing_service),
):
    """查询读者当前借阅列表"""
    return await service.get_active_borrowings_by_reader(reader_id)
