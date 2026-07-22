class PolicyError(Exception):
    """策略模块基础异常。"""


class PolicyPredictionError(PolicyError):
    """策略预测失败。"""


class UnknownPolicyProviderError(PolicyError):
    """未注册的策略 Provider。"""

    def __init__(
        self,
        provider_name: str,
    ) -> None:

        super().__init__(
            f"Unknown Policy Provider: {provider_name}",
        )

        self.provider_name = provider_name
