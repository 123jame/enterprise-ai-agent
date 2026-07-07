from abc import ABC
from abc import abstractmethod

from app.rag.types import Document
from app.rag.types import ScoredDocument


class VectorStore(ABC):
    """
    向量存储抽象接口。

    单一职责：向量的持久化与相似度检索。
    后续可替换为 FAISS、Chroma、Milvus、PGVector 等实现。
    """

    @abstractmethod
    def add(
        self,
        document: Document,
        vector: list[float],
    ) -> None:
        """
        写入或更新一条文档向量。
        """

        pass

    @abstractmethod
    def delete(
        self,
        document_id: str,
    ) -> None:
        """
        按文档 ID 删除向量。
        """

        pass

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[ScoredDocument]:
        """
        按余弦相似度检索最相关的文档。
        """

        pass
