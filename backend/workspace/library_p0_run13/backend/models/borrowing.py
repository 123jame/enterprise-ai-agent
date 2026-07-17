"""Borrowing record ORM model."""

from datetime import datetime, date
from sqlalchemy import Integer, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Borrowing(Base):
    __tablename__ = "borrowings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reader_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("readers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    borrow_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="借书时间"
    )
    due_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="应还日期（默认借书日起30天）"
    )
    return_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="实际归还时间"
    )
    is_returned: Mapped[bool] = mapped_column(
        Integer, default=False, comment="是否已归还"
    )

    # Relationships
    book = relationship("Book", back_populates="borrowings")
    reader = relationship("Reader", back_populates="borrowings")

    def __repr__(self) -> str:
        return (
            f"<Borrowing(id={self.id}, book_id={self.book_id}, "
            f"reader_id={self.reader_id}, returned={self.is_returned})>"
        )
