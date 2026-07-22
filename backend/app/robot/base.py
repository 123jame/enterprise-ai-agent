from abc import ABC
from abc import abstractmethod
from typing import Any

from app.robot.types import RobotActionResult
from app.robot.types import RobotState


class BaseRobot(ABC):
    """
    机器人能力抽象接口。

    单一职责：封装移动、抓取、释放与状态查询。
    后续可替换为 ROS、UR5、真实机械臂 SDK 等实现。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Robot Provider 名称，用于日志与 Observation 标记。"""

    @abstractmethod
    def move(
        self,
        target: str | dict[str, Any],
    ) -> RobotActionResult:
        """
        移动机器人到目标位置。

        参数:
            target: 目标位置名称（如 table）或坐标 dict（x/y/z）
        """

        pass

    @abstractmethod
    def grasp(
        self,
        target: str,
    ) -> RobotActionResult:
        """
        抓取目标物体。

        参数:
            target: 物体名称，例如 red cup
        """

        pass

    @abstractmethod
    def release(self) -> RobotActionResult:
        """释放当前抓取的物体。"""

        pass

    @abstractmethod
    def get_state(self) -> RobotState:
        """获取机器人当前状态。"""

        pass
