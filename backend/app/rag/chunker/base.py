from abc import ABC
from abc import abstractmethod

from app.rag.types import Document


class Chunker(ABC):
    """
    文档切分抽象接口。

    后续可替换为 Recursive Chunk、Token Chunk、Sliding Window 等。
    """

    @abstractmethod
    def chunk(
        self,
        document: Document,
    ) -> list[Document]:
        """
        将文档切分为更小的 Document 片段。
        """

        pass
