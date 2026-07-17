"""Pydantic schemas for Book."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    """Schema for creating a new book."""
    title: str = Field(..., max_length=255, description="书名")
    author: str = Field(..., max_length=255, description="作者")
    isbn: str = Field(..., max_length=20, description="ISBN 编号")
    publisher: Optional[str] = Field(None, max_length=255, description="出版社")
    publish_year: Optional[int] = Field(None, ge=1000, le=2100, description="出版年份")
    category: Optional[str] = Field(None, max_length=100, description="分类")
    description: Optional[str] = Field(None, description="图书简介")
    total_stock: int = Field(default=1, ge=1, description="总库存")


class BookUpdate(BaseModel):
    """Schema for updating an existing book."""
    title: Optional[str] = Field(None, max_length=255)
    author: Optional[str] = Field(None, max_length=255)
    isbn: Optional[str] = Field(None, max_length=20)
    publisher: Optional[str] = Field(None, max_length=255)
    publish_year: Optional[int] = Field(None, ge=1000, le=2100)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    total_stock: Optional[int] = Field(None, ge=1)


class BookResponse(BaseModel):
    """Schema for book response."""
    id: int
    title: str
    author: str
    isbn: str
    publisher: Optional[str] = None
    publish_year: Optional[int] = None
    category: Optional[str] = None
    description: Optional[str] = None
    total_stock: int
    available_stock: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookSearchParams(BaseModel):
    """Schema for book search query parameters."""
    keyword: Optional[str] = Field(None, description="模糊搜索（书名/作者/ISBN）")
    category: Optional[str] = Field(None, description="分类筛选")
    is_active: Optional[bool] = Field(None, description="上架状态")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
