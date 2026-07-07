from app.rag.strategy.base import RetrieverStrategy
from app.rag.types import ScoredDocument
from app.rag.vectorstore.base import VectorStore


class SimilaritySearchStrategy(RetrieverStrategy):
    """
    默认相似度检索策略。

    基于 VectorStore 的余弦相似度搜索，并按 score_threshold 过滤。
    """

    def __init__(
        self,
        vector_store: VectorStore,
    ):

        self._vector_store = vector_store

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        score_threshold: float,
    ) -> list[ScoredDocument]:

        results = self._vector_store.search(
            query_vector,
            top_k=top_k,
        )

        if score_threshold <= 0:

            return results

        return [
            result
            for result in results
            if result.score >= score_threshold
        ]
