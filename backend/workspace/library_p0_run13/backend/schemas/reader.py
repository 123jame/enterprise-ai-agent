"""Pydantic schemas for Reader."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ReaderCreate(BaseModel):
    """Schema for creating a new reader."""
    name: str = Field(..., max_length=100, description="读者姓名")
    id_card: str = Field(..., max_length=50, description="证件号")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    email: Optional[str] = Field(None, max_length=100, description="电子邮箱")


class ReaderUpdate(BaseModel):
    """Schema for updating reader info."""
    name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = Field(None, description="冻结/解冻读者账号")


class ReaderResponse(BaseModel):
    """Schema for reader response."""
    id: int
    name: str
    id_card: str
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
