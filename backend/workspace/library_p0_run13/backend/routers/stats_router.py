"""Statistics API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from repositories.borrowing_repository import BorrowingRepository
from services.stats_service import StatsService
from schemas.stats import (
    BookStatsResponse,
    ReaderStatsResponse,
    PopularBookResponse,
)

router = APIRouter(prefix="/api/stats", tags=["查询统计"])


async def get_stats_service(db: AsyncSession = Depends(get_db)) -> StatsService:
    borrowing_repo = BorrowingRepository(db)
    return StatsService(db, borrowing_repo)


@router.get("/books", response_model=BookStatsResponse)
async def get_book_stats(
    service: StatsService = Depends(get_stats_service),
):
    """图书统计：总数、分类分布、当前借出数量"""
    return await service.get_book_stats()


@router.get("/readers", response_model=ReaderStatsResponse)
async def get_reader_stats(
    service: StatsService = Depends(get_stats_service),
):
    """读者统计：读者总数、活跃读者数"""
    return await service.get_reader_stats()


@router.get("/popular-books", response_model=list)
async def get_popular_books(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    service: StatsService = Depends(get_stats_service),
):
    """热门图书借阅排行"""
    return await service.get_popular_books(limit=limit)


@router.get("/overdue")
async def get_overdue_borrowings(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: StatsService = Depends(get_stats_service),
):
    """逾期借阅清单"""
    return await service.get_overdue_borrowings(page=page, page_size=page_size)
