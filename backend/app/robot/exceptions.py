class RobotError(Exception):
    """机器人模块基础异常。"""


class RobotActionError(RobotError):
    """机器人动作执行失败。"""


class UnknownRobotProviderError(RobotError):
    """未注册的机器人 Provider。"""

    def __init__(
        self,
        provider_name: str,
    ) -> None:

        super().__init__(
            f"Unknown Robot Provider: {provider_name}",
        )

        self.provider_name = provider_name
