from abc import ABC
from abc import abstractmethod

from app.rag.types import ScoredDocument


class RetrieverStrategy(ABC):
    """
    检索策略抽象接口。

    后续可替换为 MMR、Hybrid Search、Keyword Search 等。
    也可扩展 Multi Retriever、Reranker、GraphRAG、Web Search。
    """

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
        score_threshold: float,
    ) -> list[ScoredDocument]:
        """
        根据 query 向量检索相关文档。
        """

        pass
