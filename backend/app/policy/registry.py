from app.policy.base import BasePolicy
from app.policy.mock import MockPolicy


class PolicyProviderRegistry:
    """
    策略 Provider 注册表。

    通过名称获取具体实现，便于后续接入 OpenVLA、RT-2、π0 等。
    """

    _registry: dict[
        str,
        type[BasePolicy],
    ] = {}

    @classmethod
    def register(
        cls,
        name: str,
        provider_cls: type[BasePolicy],
    ) -> None:

        cls._registry[name] = provider_cls

    @classmethod
    def get(
        cls,
        name: str,
    ) -> type[BasePolicy]:

        if name not in cls._registry:

            from app.policy.exceptions import UnknownPolicyProviderError

            raise UnknownPolicyProviderError(name)

        return cls._registry[name]

    @classmethod
    def list_providers(cls) -> list[str]:

        return sorted(cls._registry.keys())


PolicyProviderRegistry.register(
    "mock",
    MockPolicy,
)
