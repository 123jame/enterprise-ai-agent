class VisionError(Exception):
    """视觉模块基础异常。"""


class VisionProviderError(VisionError):
    """视觉 Provider 执行失败。"""


class UnknownVisionProviderError(VisionError):
    """未注册的视觉 Provider。"""

    def __init__(
        self,
        provider_name: str,
    ) -> None:

        super().__init__(
            f"Unknown Vision Provider: {provider_name}",
        )

        self.provider_name = provider_name
