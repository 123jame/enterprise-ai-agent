"""Reader API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from repositories.reader_repository import ReaderRepository
from services.reader_service import ReaderService
from schemas.reader import ReaderCreate, ReaderUpdate, ReaderResponse

router = APIRouter(prefix="/api/readers", tags=["读者管理"])


async def get_reader_service(db: AsyncSession = Depends(get_db)) -> ReaderService:
    repo = ReaderRepository(db)
    return ReaderService(repo)


@router.get("/", response_model=dict)
async def search_readers(
    keyword: str = Query(None, description="模糊搜索（姓名/证件号）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: ReaderService = Depends(get_reader_service),
):
    """查询读者列表（支持模糊搜索、分页）"""
    readers, total = await service.search_readers(
        keyword=keyword, page=page, page_size=page_size
    )
    return {
        "items": [ReaderResponse.model_validate(r) for r in readers],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{reader_id}", response_model=ReaderResponse)
async def get_reader(
    reader_id: int,
    service: ReaderService = Depends(get_reader_service),
):
    """获取读者详情"""
    reader = await service.get_reader(reader_id)
    return ReaderResponse.model_validate(reader)


@router.post("/", response_model=ReaderResponse, status_code=201)
async def create_reader(
    data: ReaderCreate,
    service: ReaderService = Depends(get_reader_service),
):
    """注册新读者（管理员）"""
    reader = await service.create_reader(data)
    return ReaderResponse.model_validate(reader)


@router.put("/{reader_id}", response_model=ReaderResponse)
async def update_reader(
    reader_id: int,
    data: ReaderUpdate,
    service: ReaderService = Depends(get_reader_service),
):
    """更新读者信息 / 冻结/解冻读者（管理员）"""
    reader = await service.update_reader(reader_id, data)
    return ReaderResponse.model_validate(reader)
