import json
from typing import Any

from app.robot.base import BaseRobot
from app.robot.exceptions import RobotActionError
from app.robot.factory import get_robot
from app.robot.types import RobotActionResult
from app.tools.base_tool import BaseTool
from app.tools.types import ToolContext
from app.tools.types import ToolResult


def build_robot_observation_content(
    result: RobotActionResult,
) -> str:
    """
    将机器人动作结果格式化为 Observation 友好内容。

    后续 Observation 模块可直接解析 type=robot 的结构化反馈。
    """

    payload = {
        "type": "robot",
        "content": result.message,
        "action": result.action,
        "success": result.success,
        "provider": result.provider,
        "state": {
            "position": result.state.position,
            "holding": result.state.holding,
            "status": result.state.status,
        },
        "metadata": result.metadata,
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
    )


class RobotMoveTool(BaseTool):
    """
    机器人移动 Tool。

    调用链：Agent -> RobotMoveTool -> BaseRobot.move() -> Observation
    """

    def __init__(
        self,
        robot: BaseRobot | None = None,
    ) -> None:

        self._robot = robot or get_robot()

    @property
    def name(self) -> str:

        return "robot_move"

    @property
    def description(self) -> str:

        return (
            "Move the robot to a target location. "
            "Target can be a named place such as 'table', "
            "or coordinates x/y/z."
        )

    @property
    def schema(self) -> dict[str, Any]:

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": (
                                "Named location, e.g. table/home/shelf, "
                                "or coordinate string 'x,y,z'."
                            ),
                        },
                        "x": {
                            "type": "number",
                            "description": "Target X coordinate.",
                        },
                        "y": {
                            "type": "number",
                            "description": "Target Y coordinate.",
                        },
                        "z": {
                            "type": "number",
                            "description": "Target Z coordinate.",
                        },
                    },
                    "required": ["target"],
                },
            },
        }

    def execute(
        self,
        context: ToolContext,
    ) -> ToolResult:

        arguments = context.arguments or {}
        target = arguments.get("target")

        if target is None and not self._has_coordinates(arguments):

            return ToolResult(
                success=False,
                content="Missing required argument: target",
            )

        move_target = self._resolve_move_target(arguments)

        try:

            result = self._robot.move(move_target)

        except RobotActionError as error:

            return ToolResult(
                success=False,
                content=str(error),
            )

        return ToolResult(
            success=result.success,
            content=build_robot_observation_content(result),
        )

    def _has_coordinates(
        self,
        arguments: dict[str, Any],
    ) -> bool:

        return all(
            key in arguments and arguments[key] is not None
            for key in ("x", "y", "z")
        )

    def _resolve_move_target(
        self,
        arguments: dict[str, Any],
    ) -> str | dict[str, float]:

        if self._has_coordinates(arguments):

            return {
                "x": float(arguments["x"]),
                "y": float(arguments["y"]),
                "z": float(arguments["z"]),
            }

        return str(arguments.get("target", "")).strip()


class RobotGraspTool(BaseTool):
    """
    机器人抓取 Tool。
    """

    def __init__(
        self,
        robot: BaseRobot | None = None,
    ) -> None:

        self._robot = robot or get_robot()

    @property
    def name(self) -> str:

        return "robot_grasp"

    @property
    def description(self) -> str:

        return (
            "Grasp a target object with the robot gripper, "
            "for example 'red cup'."
        )

    @property
    def schema(self) -> dict[str, Any]:

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": (
                                "Object name to grasp, e.g. red cup."
                            ),
                        },
                    },
                    "required": ["target"],
                },
            },
        }

    def execute(
        self,
        context: ToolContext,
    ) -> ToolResult:

        arguments = context.arguments or {}
        target = arguments.get("target")

        if not target:

            return ToolResult(
                success=False,
                content="Missing required argument: target",
            )

        result = self._robot.grasp(str(target))

        return ToolResult(
            success=result.success,
            content=build_robot_observation_content(result),
        )


class RobotReleaseTool(BaseTool):
    """
    机器人释放 Tool。
    """

    def __init__(
        self,
        robot: BaseRobot | None = None,
    ) -> None:

        self._robot = robot or get_robot()

    @property
    def name(self) -> str:

        return "robot_release"

    @property
    def description(self) -> str:

        return "Release the object currently held by the robot gripper."

    @property
    def schema(self) -> dict[str, Any]:

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        }

    def execute(
        self,
        context: ToolContext,
    ) -> ToolResult:

        result = self._robot.release()

        return ToolResult(
            success=result.success,
            content=build_robot_observation_content(result),
        )
