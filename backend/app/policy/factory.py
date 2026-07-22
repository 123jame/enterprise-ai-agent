import os

from app.policy.base import BasePolicy
from app.policy.registry import PolicyProviderRegistry


_policy_instance: BasePolicy | None = None


def get_policy(
    provider_name: str | None = None,
) -> BasePolicy:
    """
    获取策略模型实例。

    默认读取环境变量 POLICY_PROVIDER，未配置时使用 mock。
    """

    global _policy_instance

    if _policy_instance is not None and provider_name is None:

        return _policy_instance

    selected = provider_name or os.getenv(
        "POLICY_PROVIDER",
        "mock",
    )

    provider_cls = PolicyProviderRegistry.get(selected)
    instance = provider_cls()

    if provider_name is None:

        _policy_instance = instance

    return instance


def reset_policy() -> None:
    """测试辅助：重置 Policy 单例。"""

    global _policy_instance

    _policy_instance = None
