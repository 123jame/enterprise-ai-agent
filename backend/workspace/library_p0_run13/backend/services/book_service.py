"""Book business logic layer."""

from typing import Optional, Tuple, List
from fastapi import HTTPException, status

from models.book import Book
from schemas.book import BookCreate, BookUpdate, BookSearchParams
from repositories.book_repository import BookRepository


class BookService:
    """Service handling book business rules."""

    def __init__(self, repo: BookRepository):
        self.repo = repo

    async def create_book(self, data: BookCreate) -> Book:
        """Create a new book. Validates ISBN uniqueness."""
        existing = await self.repo.get_by_isbn(data.isbn)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"ISBN '{data.isbn}' 已存在",
            )

        book = Book(
            title=data.title,
            author=data.author,
            isbn=data.isbn,
            publisher=data.publisher,
            publish_year=data.publish_year,
            category=data.category,
            description=data.description,
            total_stock=data.total_stock,
            available_stock=data.total_stock,
        )
        return await self.repo.create(book)

    async def get_book(self, book_id: int) -> Book:
        book = await self.repo.get_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="图书不存在",
            )
        return book

    async def update_book(self, book_id: int, data: BookUpdate) -> Book:
        """Update a book. Recalculates available_stock if total_stock changes."""
        book = await self.get_book(book_id)

        update_data = data.model_dump(exclude_unset=True)

        # If total_stock changes, adjust available_stock delta
        if "total_stock" in update_data:
            new_total = update_data["total_stock"]
            diff = new_total - book.total_stock
            new_available = book.available_stock + diff
            if new_available < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="调整后的总库存不能低于当前已借出数量",
                )
            book.total_stock = new_total
            book.available_stock = new_available

        # Update other fields
        for field, value in update_data.items():
            if field != "total_stock":
                setattr(book, field, value)

        return await self.repo.update(book)

    async def deactivate_book(self, book_id: int) -> Book:
        """Mark a book as deactivated (off-shelf)."""
        book = await self.get_book(book_id)
        if not book.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="图书已处于下架状态",
            )
        if book.available_stock < book.total_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="尚有图书被借出，无法下架",
            )
        book.is_active = False
        return await self.repo.update(book)

    async def activate_book(self, book_id: int) -> Book:
        """Mark a book as active (on-shelf)."""
        book = await self.get_book(book_id)
        book.is_active = True
        return await self.repo.update(book)

    async def search_books(
        self, params: BookSearchParams
    ) -> Tuple[List[Book], int]:
        return await self.repo.search(
            keyword=params.keyword,
            category=params.category,
            is_active=params.is_active,
            page=params.page,
            page_size=params.page_size,
        )
