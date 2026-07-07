from app.rag.compression.base import ContextCompressor
from app.rag.types import ScoredDocument


class NoCompression(ContextCompressor):
    """
    默认不压缩，直接返回原始检索结果。
    """

    def compress(
        self,
        documents: list[ScoredDocument],
    ) -> list[ScoredDocument]:

        return documents
