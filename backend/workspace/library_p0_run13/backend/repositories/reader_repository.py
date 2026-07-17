"""Reader data access layer."""

from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.reader import Reader


class ReaderRepository:
    """Repository handling Reader database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, reader: Reader) -> Reader:
        self.session.add(reader)
        await self.session.flush()
        return reader

    async def get_by_id(self, reader_id: int) -> Optional[Reader]:
        stmt = select(Reader).where(Reader.id == reader_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_card(self, id_card: str) -> Optional[Reader]:
        stmt = select(Reader).where(Reader.id_card == id_card)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Reader], int]:
        """Search readers with keyword (name/id_card) and pagination."""
        query = select(Reader)

        if keyword:
            like_pattern = f"%{keyword}%"
            query = query.where(
                or_(
                    Reader.name.ilike(like_pattern),
                    Reader.id_card.ilike(like_pattern),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Paginate
        offset = (page - 1) * page_size
        query = query.order_by(Reader.id.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(query)
        readers = list(result.scalars().all())

        return readers, total

    async def update(self, reader: Reader) -> Reader:
        self.session.add(reader)
        await self.session.flush()
        return reader
