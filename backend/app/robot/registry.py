from app.robot.base import BaseRobot
from app.robot.mock import MockRobot


class RobotProviderRegistry:
    """
    机器人 Provider 注册表。

    通过名称获取具体实现，便于后续接入 ROS、UR5 等真实机器人。
    """

    _registry: dict[
        str,
        type[BaseRobot],
    ] = {}

    @classmethod
    def register(
        cls,
        name: str,
        provider_cls: type[BaseRobot],
    ) -> None:

        cls._registry[name] = provider_cls

    @classmethod
    def get(
        cls,
        name: str,
    ) -> type[BaseRobot]:

        if name not in cls._registry:

            from app.robot.exceptions import UnknownRobotProviderError

            raise UnknownRobotProviderError(name)

        return cls._registry[name]

    @classmethod
    def list_providers(cls) -> list[str]:

        return sorted(cls._registry.keys())


RobotProviderRegistry.register(
    "mock",
    MockRobot,
)
