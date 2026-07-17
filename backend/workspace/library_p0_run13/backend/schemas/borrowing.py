"""Pydantic schemas for Borrowing."""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field


class BorrowRequest(BaseModel):
    """Schema for borrowing a book."""
    book_id: int = Field(..., description="图书 ID")
    reader_id: int = Field(..., description="读者 ID")


class ReturnRequest(BaseModel):
    """Schema for returning a book."""
    borrowing_id: int = Field(..., description="借阅记录 ID")


class BorrowingResponse(BaseModel):
    """Schema for borrowing record response."""
    id: int
    book_id: int
    reader_id: int
    borrow_date: datetime
    due_date: date
    return_date: Optional[datetime] = None
    is_returned: bool

    class Config:
        from_attributes = True


class ActiveBorrowingResponse(BaseModel):
    """Schema for active (not yet returned) borrowing record."""
    id: int
    book_id: int
    book_title: str = Field(..., description="书名")
    reader_id: int
    reader_name: str = Field(..., description="读者姓名")
    borrow_date: datetime
    due_date: date
    is_overdue: bool = Field(..., description="是否逾期")
    overdue_days: int = Field(default=0, description="逾期天数")
