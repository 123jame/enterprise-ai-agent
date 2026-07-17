"""Reader ORM model."""

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Reader(Base):
    __tablename__ = "readers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="读者姓名")
    id_card: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="证件号"
    )
    phone: Mapped[str] = mapped_column(String(20), nullable=True, comment="联系电话")
    email: Mapped[str] = mapped_column(String(100), nullable=True, comment="电子邮箱")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否有效（未冻结）")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="注册时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # Relationships
    borrowings = relationship("Borrowing", back_populates="reader")

    def __repr__(self) -> str:
        return f"<Reader(id={self.id}, name='{self.name}', id_card='{self.id_card}')>"
