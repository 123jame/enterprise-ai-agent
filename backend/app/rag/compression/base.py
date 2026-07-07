from abc import ABC
from abc import abstractmethod

from app.rag.types import ScoredDocument


class ContextCompressor(ABC):
    """
    检索结果压缩抽象接口。

    预留 Context Window Optimization 能力。
    后续可替换为摘要压缩、Token 截断等实现。
    """

    @abstractmethod
    def compress(
        self,
        documents: list[ScoredDocument],
    ) -> list[ScoredDocument]:
        """
        压缩检索结果以适应上下文窗口。
        """

        pass
