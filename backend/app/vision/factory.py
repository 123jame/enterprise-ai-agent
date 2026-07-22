import os

from app.vision.base import BaseVisionProvider
from app.vision.registry import VisionProviderRegistry


_vision_provider_instance: BaseVisionProvider | None = None


def get_vision_provider(
    provider_name: str | None = None,
) -> BaseVisionProvider:
    """
    获取视觉 Provider 单例。

    默认读取环境变量 VISION_PROVIDER，未配置时使用 mock。
    """

    global _vision_provider_instance

    if _vision_provider_instance is not None and provider_name is None:

        return _vision_provider_instance

    selected = provider_name or os.getenv(
        "VISION_PROVIDER",
        "mock",
    )

    provider_cls = VisionProviderRegistry.get(selected)
    instance = provider_cls()

    if provider_name is None:

        _vision_provider_instance = instance

    return instance


def reset_vision_provider() -> None:
    """测试辅助：重置 Provider 单例。"""

    global _vision_provider_instance

    _vision_provider_instance = None
