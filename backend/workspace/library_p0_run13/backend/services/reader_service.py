"""Reader business logic layer."""

from typing import Optional, Tuple, List
from fastapi import HTTPException, status

from models.reader import Reader
from schemas.reader import ReaderCreate, ReaderUpdate
from repositories.reader_repository import ReaderRepository


class ReaderService:
    """Service handling reader business rules."""

    def __init__(self, repo: ReaderRepository):
        self.repo = repo

    async def create_reader(self, data: ReaderCreate) -> Reader:
        """Create a new reader. Validates id_card uniqueness."""
        existing = await self.repo.get_by_id_card(data.id_card)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"证件号 '{data.id_card}' 已存在",
            )

        reader = Reader(
            name=data.name,
            id_card=data.id_card,
            phone=data.phone,
            email=data.email,
        )
        return await self.repo.create(reader)

    async def get_reader(self, reader_id: int) -> Reader:
        reader = await self.repo.get_by_id(reader_id)
        if not reader:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="读者不存在",
            )
        return reader

    async def update_reader(self, reader_id: int, data: ReaderUpdate) -> Reader:
        reader = await self.get_reader(reader_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(reader, field, value)
        return await self.repo.update(reader)

    async def search_readers(
        self,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Reader], int]:
        return await self.repo.search(
            keyword=keyword,
            page=page,
            page_size=page_size,
        )
