from abc import ABC
from abc import abstractmethod

from app.memory.types import MemoryContext
from app.memory.types import MemoryRecord


class BaseMemory(ABC):
    """
    Memory抽象接口
    """

    @abstractmethod
    def load(
        self,
        session_id: str
    ) -> MemoryContext:
        """
        读取Memory
        """
        pass

    @abstractmethod
    def save(
        self,
        session_id: str,
        record: MemoryRecord
    ) -> None:
        """
        保存一条记录
        """
        pass

    @abstractmethod
    def clear(
        self,
        session_id: str
    ) -> None:
        """
        清空Memory
        """
        pass