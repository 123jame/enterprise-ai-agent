from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any


class RobotProviderType(str, Enum):
    """
    机器人提供方类型。

    当前仅实现 MOCK；其余类型预留，便于后续接入真实机器人。
    """

    MOCK = "mock"

    # 预留扩展：ROS / UR / 真实机械臂 SDK
    ROS = "ros"
    UR5 = "ur5"
    GENERIC_ARM = "generic_arm"


@dataclass
class RobotState:
    """
    机器人当前状态。

    供 Agent 与 Observation 模块读取环境反馈。
    """

    provider: str

    position: dict[str, float]

    holding: str | None = None

    status: str = "idle"

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


@dataclass
class RobotActionResult:
    """
    机器人动作执行结果。
    """

    success: bool

    action: str

    message: str

    provider: str

    state: RobotState

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )
