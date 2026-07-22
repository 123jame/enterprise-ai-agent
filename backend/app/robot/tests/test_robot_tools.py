"""
Task13.4 Robot Tool 测试。

运行:
    cd backend
    python -m app.robot.tests.test_robot_tools
"""

from __future__ import annotations

import json

from app.robot.factory import reset_robot
from app.robot.mock import MockRobot
from app.robot.robot_tools import RobotGraspTool
from app.robot.robot_tools import RobotMoveTool
from app.robot.robot_tools import RobotReleaseTool
from app.robot.tool_registrar import register_robot_tools
from app.robot.tool_registrar import reset_robot_tool_registration
from app.tools.factory import ToolFactory
from app.tools.manager import ToolManager
from app.tools.registry import ToolRegistry
from app.tools.types import ToolContext


def test_robot_tool_names_and_schemas() -> None:

    robot = MockRobot()

    move_tool = RobotMoveTool(robot)
    grasp_tool = RobotGraspTool(robot)
    release_tool = RobotReleaseTool(robot)

    assert move_tool.name == "robot_move"
    assert grasp_tool.name == "robot_grasp"
    assert release_tool.name == "robot_release"

    assert "target" in move_tool.schema["function"]["parameters"]["properties"]
    assert "target" in grasp_tool.schema["function"]["parameters"]["properties"]
    assert release_tool.schema["function"]["parameters"]["properties"] == {}


def test_robot_tools_shared_state_flow() -> None:

    robot = MockRobot()
    move_tool = RobotMoveTool(robot)
    grasp_tool = RobotGraspTool(robot)
    release_tool = RobotReleaseTool(robot)

    move_result = move_tool.execute(
        ToolContext(
            tool_name="robot_move",
            arguments={"target": "table"},
        )
    )

    assert move_result.success is True

    move_payload = json.loads(move_result.content)

    assert move_payload["type"] == "robot"
    assert move_payload["action"] == "move"

    grasp_result = grasp_tool.execute(
        ToolContext(
            tool_name="robot_grasp",
            arguments={"target": "red cup"},
        )
    )

    assert grasp_result.success is True

    grasp_payload = json.loads(grasp_result.content)

    assert grasp_payload["content"] == "grasp success: red cup"
    assert grasp_payload["state"]["holding"] == "red cup"

    release_result = release_tool.execute(
        ToolContext(
            tool_name="robot_release",
            arguments={},
        )
    )

    assert release_result.success is True

    release_payload = json.loads(release_result.content)

    assert release_payload["content"] == "release success: red cup"
    assert release_payload["state"]["holding"] is None


def test_robot_move_with_coordinates() -> None:

    robot = MockRobot()
    tool = RobotMoveTool(robot)

    result = tool.execute(
        ToolContext(
            tool_name="robot_move",
            arguments={
                "target": "ignored-when-coords-present",
                "x": 1.5,
                "y": 2.5,
                "z": 0.5,
            },
        )
    )

    assert result.success is True

    payload = json.loads(result.content)

    assert payload["state"]["position"] == {
        "x": 1.5,
        "y": 2.5,
        "z": 0.5,
    }


def test_tool_registry_and_manager_integration() -> None:

    reset_robot()
    reset_robot_tool_registration()
    ToolFactory._initialized = False

    ToolFactory.initialize()

    for tool_name in ("robot_move", "robot_grasp", "robot_release"):

        tool = ToolRegistry.get(tool_name)

        assert tool.name == tool_name

    schemas = ToolManager().get_schemas()
    schema_names = [
        item["function"]["name"]
        for item in schemas
    ]

    assert "robot_move" in schema_names
    assert "robot_grasp" in schema_names
    assert "robot_release" in schema_names

    manager = ToolManager()

    move_result = manager.execute(
        ToolContext(
            tool_name="robot_move",
            arguments={"target": "table"},
        )
    )
    grasp_result = manager.execute(
        ToolContext(
            tool_name="robot_grasp",
            arguments={"target": "red cup"},
        )
    )

    assert move_result.success is True
    assert grasp_result.success is True

    grasp_payload = json.loads(grasp_result.content)

    assert grasp_payload["type"] == "robot"
    assert "grasp success" in grasp_payload["content"]


def run_all_tests() -> None:

    test_robot_tool_names_and_schemas()
    test_robot_tools_shared_state_flow()
    test_robot_move_with_coordinates()
    test_tool_registry_and_manager_integration()

    print("Task13.4 Robot Tool tests passed.")


if __name__ == "__main__":

    run_all_tests()
