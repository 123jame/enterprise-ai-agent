from abc import ABC
from abc import abstractmethod


class EmbeddingProvider(ABC):
    """
    Embedding 模型抽象接口。

    单一职责：将文本转换为向量。
    后续可替换为 OpenAI、BGE、Jina 等实现。
    """

    @abstractmethod
    def embed(
        self,
        text: str,
    ) -> list[float]:
        """
        将单条文本转换为 embedding 向量。
        """

        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        向量维度，供 VectorStore 校验使用。
        """

        pass
