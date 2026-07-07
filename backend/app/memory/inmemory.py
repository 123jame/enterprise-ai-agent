from app.memory.base import BaseMemory
from app.memory.types import MemoryContext
from app.memory.types import MemoryRecord


class InMemory(BaseMemory):
    """
    基于 Python 内存的 Memory 实现
    """

    def __init__(self):

        # {
        #   "session_id": [
        #       MemoryRecord(...),
        #       MemoryRecord(...)
        #   ]
        # }

        self._memory: dict[
            str,
            list[MemoryRecord]
        ] = {}

    def load(
        self,
        session_id: str
    ) -> MemoryContext:

        records = self._memory.get(
            session_id,
            []
        )

        return MemoryContext(

            session_id=session_id,

            records=records.copy()

        )

    def save(
        self,
        session_id: str,
        record: MemoryRecord
    ) -> None:

        if session_id not in self._memory:

            self._memory[session_id] = []

        self._memory[session_id].append(
            record
        )

    def clear(
        self,
        session_id: str
    ) -> None:

        self._memory.pop(
            session_id,
            None
        )