"""
Task13.5 Observation Module 测试。

运行:
    cd backend
    python -m app.embodied.tests.test_observation
"""

from __future__ import annotations

import json

from app.embodied.observation_factory import ObservationFactory
from app.embodied.types import Observation
from app.embodied.types import ObservationType
from app.robot.robot_tools import RobotGraspTool
from app.robot.mock import MockRobot
from app.tools.types import ToolContext
from app.tools.types import ToolResult
from app.vision.vision_tool import AnalyzeImageTool


def test_observation_vision_example() -> None:

    observation = ObservationFactory.vision(
        "red cup detected",
        source="analyze_image",
    )

    assert observation.type == "vision"
    assert observation.content == "red cup detected"
    assert observation.to_dict() == {
        "type": "vision",
        "content": "red cup detected",
        "success": True,
        "source": "analyze_image",
    }


def test_observation_robot_example() -> None:

    observation = ObservationFactory.robot(
        "grasp success",
        source="robot_grasp",
    )

    assert observation.type == "robot"
    assert observation.content == "grasp success"
    assert "robot" in observation.to_prompt_text()


def test_from_payload_with_metadata() -> None:

    payload = {
        "type": "vision",
        "content": "red cup detected",
        "analysis": "table scene",
        "detected_objects": ["red cup"],
    }

    observation = ObservationFactory.from_payload(payload)

    assert observation.type == ObservationType.VISION.value
    assert observation.content == "red cup detected"
    assert observation.metadata["detected_objects"] == ["red cup"]


def test_from_tool_result_with_analyze_image() -> None:

    tool = AnalyzeImageTool()
    tool_result = tool.execute(
        ToolContext(
            tool_name="analyze_image",
            arguments={
                "image": "mock-image",
                "prompt": "找红色杯子",
            },
        )
    )

    observation = ObservationFactory.from_tool_result(
        tool_result,
        tool_name="analyze_image",
    )

    assert observation.type == "vision"
    assert "red cup" in observation.content
    assert observation.success is True
    assert observation.source == "analyze_image"
    assert observation.raw is not None


def test_from_tool_result_with_robot_grasp() -> None:

    robot = MockRobot()
    tool = RobotGraspTool(robot)
    tool_result = tool.execute(
        ToolContext(
            tool_name="robot_grasp",
            arguments={"target": "red cup"},
        )
    )

    observation = ObservationFactory.from_tool_result(
        tool_result,
        tool_name="robot_grasp",
    )

    assert observation.type == "robot"
    assert observation.content == "grasp success: red cup"
    assert observation.metadata["action"] == "grasp"
    assert observation.metadata["state"]["holding"] == "red cup"


def test_from_tool_result_error() -> None:

    observation = ObservationFactory.from_tool_result(
        ToolResult(
            success=False,
            content="Missing required argument: target",
        ),
        tool_name="robot_grasp",
    )

    assert observation.type == "error"
    assert observation.success is False
    assert "Missing required argument" in observation.content


def test_from_tool_result_plain_tool() -> None:

    observation = ObservationFactory.from_tool_result(
        ToolResult(
            success=True,
            content="2026-07-22 12:00:00",
        ),
        tool_name="time",
    )

    assert observation.type == "tool"
    assert observation.content == "2026-07-22 12:00:00"


def test_to_json_and_prompt_text() -> None:

    observation = Observation(
        type="robot",
        content="grasp success",
        source="robot_grasp",
    )

    payload = json.loads(observation.to_json())

    assert payload["type"] == "robot"
    assert payload["content"] == "grasp success"
    assert observation.to_prompt_text().startswith(
        "[Observation:robot:success][source=robot_grasp]"
    )


def run_all_tests() -> None:

    test_observation_vision_example()
    test_observation_robot_example()
    test_from_payload_with_metadata()
    test_from_tool_result_with_analyze_image()
    test_from_tool_result_with_robot_grasp()
    test_from_tool_result_error()
    test_from_tool_result_plain_tool()
    test_to_json_and_prompt_text()

    print("Task13.5 Observation Module tests passed.")


if __name__ == "__main__":

    run_all_tests()
