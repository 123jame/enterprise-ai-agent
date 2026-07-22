import os

from app.robot.base import BaseRobot
from app.robot.registry import RobotProviderRegistry


_robot_instance: BaseRobot | None = None


def get_robot(
    provider_name: str | None = None,
) -> BaseRobot:
    """
    获取机器人实例。

    默认读取环境变量 ROBOT_PROVIDER，未配置时使用 mock。
    """

    global _robot_instance

    if _robot_instance is not None and provider_name is None:

        return _robot_instance

    selected = provider_name or os.getenv(
        "ROBOT_PROVIDER",
        "mock",
    )

    provider_cls = RobotProviderRegistry.get(selected)
    instance = provider_cls()

    if provider_name is None:

        _robot_instance = instance

    return instance


def reset_robot() -> None:
    """测试辅助：重置 Robot 单例。"""

    global _robot_instance

    _robot_instance = None
