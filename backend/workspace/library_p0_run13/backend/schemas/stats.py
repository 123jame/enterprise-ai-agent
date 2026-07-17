"""Pydantic schemas for statistics."""

from typing import List, Optional
from pydantic import BaseModel, Field


class BookStatsResponse(BaseModel):
    """Schema for book statistics."""
    total_books: int = Field(..., description="图书总数（上架）")
    total_categories: int = Field(..., description="分类数量")
    category_distribution: List[dict] = Field(
        default_factory=list, description="各分类图书数量"
    )
    currently_borrowed: int = Field(..., description="当前借出数量")


class ReaderStatsResponse(BaseModel):
    """Schema for reader statistics."""
    total_readers: int = Field(..., description="读者总数")
    active_readers: int = Field(..., description="活跃读者数（当前有借阅行为）")


class PopularBookResponse(BaseModel):
    """Schema for popular book ranking."""
    book_id: int
    title: str
    author: str
    borrow_count: int = Field(..., description="借阅次数")


class OverdueBorrowingResponse(BaseModel):
    """Schema for overdue borrowing item."""
    borrowing_id: int
    book_title: str
    reader_name: str
    reader_id_card: str
    borrow_date: str
    due_date: str
    overdue_days: int = Field(..., description="逾期天数")
