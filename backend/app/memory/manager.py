from app.memory.factory import get_memory
from app.memory.types import MemoryContext
from app.memory.types import MemoryRecord


class MemoryManager:

    def __init__(self):

        self.memory = get_memory()

    def load(
        self,
        session_id: str
    ) -> MemoryContext:

        return self.memory.load(
            session_id
        )

    def save_user_message(
        self,
        session_id: str,
        content: str
    ) -> None:

        record = MemoryRecord(

            role="user",

            content=content

        )

        self.memory.save(

            session_id,

            record

        )

    def save_assistant_message(
        self,
        session_id: str,
        content: str
    ) -> None:

        record = MemoryRecord(

            role="assistant",

            content=content

        )

        self.memory.save(

            session_id,

            record

        )

    def clear(
        self,
        session_id: str
    ) -> None:

        self.memory.clear(
            session_id
        )