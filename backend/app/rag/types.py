from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass
class Document:
    """
    RAG 知识库中的文档单元。

    表示一段可被索引、检索的文本内容。
    后续 Chunker 会将 Document 切分为更小的片段再写入 VectorStore。
    """

    id: str

    content: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ScoredDocument:
    """
    带相似度分数的检索结果。
    """

    document: Document

    score: float

