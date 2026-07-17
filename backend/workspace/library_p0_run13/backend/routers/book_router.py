"""Book API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from repositories.book_repository import BookRepository
from services.book_service import BookService
from schemas.book import BookCreate, BookUpdate, BookResponse, BookSearchParams

router = APIRouter(prefix="/api/books", tags=["图书管理"])


async def get_book_service(db: AsyncSession = Depends(get_db)) -> BookService:
    repo = BookRepository(db)
    return BookService(repo)


@router.get("/", response_model=dict)
async def search_books(
    keyword: str = Query(None, description="模糊搜索（书名/作者/ISBN）"),
    category: str = Query(None, description="分类筛选"),
    is_active: bool = Query(None, description="上架状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: BookService = Depends(get_book_service),
):
    """搜索图书（支持模糊查询、分类筛选、分页）"""
    params = BookSearchParams(
        keyword=keyword,
        category=category,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    books, total = await service.search_books(params)
    return {
        "items": [BookResponse.model_validate(b) for b in books],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
):
    """获取图书详情"""
    book = await service.get_book(book_id)
    return BookResponse.model_validate(book)


@router.post("/", response_model=BookResponse, status_code=201)
async def create_book(
    data: BookCreate,
    service: BookService = Depends(get_book_service),
):
    """新增图书（管理员）"""
    book = await service.create_book(data)
    return BookResponse.model_validate(book)


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    data: BookUpdate,
    service: BookService = Depends(get_book_service),
):
    """编辑图书信息（管理员）"""
    book = await service.update_book(book_id, data)
    return BookResponse.model_validate(book)


@router.patch("/{book_id}/deactivate", response_model=BookResponse)
async def deactivate_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
):
    """下架图书（管理员）"""
    book = await service.deactivate_book(book_id)
    return BookResponse.model_validate(book)


@router.patch("/{book_id}/activate", response_model=BookResponse)
async def activate_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
):
    """上架图书（管理员）"""
    book = await service.activate_book(book_id)
    return BookResponse.model_validate(book)
