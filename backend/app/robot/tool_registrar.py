from app.robot.factory import get_robot
from app.robot.robot_tools import RobotGraspTool
from app.robot.robot_tools import RobotMoveTool
from app.robot.robot_tools import RobotReleaseTool
from app.tools.registry import ToolRegistry


_robot_tools_registered = False


def register_robot_tools() -> None:
    """
    将 Robot Tool 注册到全局 ToolRegistry。

    三个 Tool 共享同一个 Robot 实例，保证 move/grasp/release 状态连续。
    """

    global _robot_tools_registered

    if _robot_tools_registered:

        return

    robot = get_robot()

    ToolRegistry.register(
        RobotMoveTool(robot),
    )
    ToolRegistry.register(
        RobotGraspTool(robot),
    )
    ToolRegistry.register(
        RobotReleaseTool(robot),
    )

    _robot_tools_registered = True


def reset_robot_tool_registration() -> None:
    """测试辅助：允许重复注册。"""

    global _robot_tools_registered

    _robot_tools_registered = False
