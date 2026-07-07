import hashlib
import struct

from app.rag.embedding.base import EmbeddingProvider


class FakeEmbeddingProvider(EmbeddingProvider):
    """
    测试用 Embedding 实现。

    基于文本哈希生成确定性向量，不依赖外部 API。
    相同文本始终返回相同向量，便于本地开发与单元测试。
    """

    def __init__(
        self,
        dimension: int = 128,
    ):

        self._dimension = dimension

    @property
    def dimension(self) -> int:

        return self._dimension

    def embed(
        self,
        text: str,
    ) -> list[float]:

        if not text:

            return [0.0] * self._dimension

        seed = hashlib.sha256(
            text.encode("utf-8")
        ).digest()

        vector: list[float] = []

        while len(vector) < self._dimension:

            chunk = seed + struct.pack(
                "<I",
                len(vector),
            )

            seed = hashlib.sha256(chunk).digest()

            for index in range(
                0,
                len(seed),
                4,
            ):

                if len(vector) >= self._dimension:

                    break

                value = struct.unpack(
                    "<I",
                    seed[index:index + 4],
                )[0]

                normalized = (value / 4294967295.0) * 2 - 1

                vector.append(normalized)

        return vector
