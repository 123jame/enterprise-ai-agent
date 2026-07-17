"""Book ORM model."""

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="书名")
    author: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="作者")
    isbn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="ISBN 编号")
    publisher: Mapped[str] = mapped_column(String(255), nullable=True, comment="出版社")
    publish_year: Mapped[int] = mapped_column(Integer, nullable=True, comment="出版年份")
    category: Mapped[str] = mapped_column(String(100), nullable=True, index=True, comment="分类")
    description: Mapped[str] = mapped_column(Text, nullable=True, comment="图书简介")
    total_stock: Mapped[int] = mapped_column(Integer, default=1, comment="总库存")
    available_stock: Mapped[int] = mapped_column(Integer, default=1, comment="可借库存")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否上架")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # Relationships
    borrowings = relationship("Borrowing", back_populates="book")

    def __repr__(self) -> str:
        return f"<Book(id={self.id}, title='{self.title}', isbn='{self.isbn}')>"
