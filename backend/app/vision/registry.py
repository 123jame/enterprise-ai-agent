from app.vision.base import BaseVisionProvider
from app.vision.mock import MockVisionProvider


class VisionProviderRegistry:
    """
    视觉 Provider 注册表。

    通过名称获取具体实现，便于后续接入 OpenAI Vision、Qwen-VL 等。
    """

    _registry: dict[
        str,
        type[BaseVisionProvider],
    ] = {}

    @classmethod
    def register(
        cls,
        name: str,
        provider_cls: type[BaseVisionProvider],
    ) -> None:

        cls._registry[name] = provider_cls

    @classmethod
    def get(
        cls,
        name: str,
    ) -> type[BaseVisionProvider]:

        if name not in cls._registry:

            from app.vision.exceptions import UnknownVisionProviderError

            raise UnknownVisionProviderError(name)

        return cls._registry[name]

    @classmethod
    def list_providers(cls) -> list[str]:

        return sorted(cls._registry.keys())


VisionProviderRegistry.register(
    "mock",
    MockVisionProvider,
)
