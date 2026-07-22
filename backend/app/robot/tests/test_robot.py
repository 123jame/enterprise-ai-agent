"""
Task13.3 Robot Module 测试。

运行:
    cd backend
    python -m app.robot.tests.test_robot
"""

from __future__ import annotations

from app.robot.factory import get_robot
from app.robot.factory import reset_robot
from app.robot.mock import MockRobot
from app.robot.registry import RobotProviderRegistry


def test_mock_robot_name() -> None:

    robot = MockRobot()

    assert robot.name == "mock"


def test_move_to_named_location() -> None:

    robot = MockRobot()

    result = robot.move("table")

    assert result.success is True
    assert result.action == "move"
    assert result.state.position["x"] == 0.8
    assert result.state.position["z"] == 0.75


def test_move_to_coordinates_dict() -> None:

    robot = MockRobot()

    result = robot.move(
        {
            "x": 1.0,
            "y": 2.0,
            "z": 0.5,
        }
    )

    assert result.success is True
    assert result.state.position == {
        "x": 1.0,
        "y": 2.0,
        "z": 0.5,
    }


def test_grasp_and_release_flow() -> None:

    robot = MockRobot()

    grasp_result = robot.grasp("red cup")

    assert grasp_result.success is True
    assert grasp_result.message == "grasp success: red cup"
    assert robot.get_state().holding == "red cup"

    release_result = robot.release()

    assert release_result.success is True
    assert release_result.message == "release success: red cup"
    assert robot.get_state().holding is None


def test_grasp_while_holding_fails() -> None:

    robot = MockRobot()

    robot.grasp("red cup")
    second_grasp = robot.grasp("blue bottle")

    assert second_grasp.success is False
    assert "请先 release" in second_grasp.message


def test_release_without_holding_fails() -> None:

    robot = MockRobot()

    result = robot.release()

    assert result.success is False
    assert "没有抓取物体" in result.message


def test_get_state() -> None:

    robot = MockRobot()

    robot.move("table")
    robot.grasp("red cup")

    state = robot.get_state()

    assert state.provider == "mock"
    assert state.holding == "red cup"
    assert state.status == "idle"
    assert state.metadata["mode"] == "mock"


def test_registry_and_factory() -> None:

    reset_robot()

    assert "mock" in RobotProviderRegistry.list_providers()

    robot = get_robot("mock")

    assert isinstance(robot, MockRobot)

    singleton = get_robot()

    assert singleton is get_robot()


def run_all_tests() -> None:

    test_mock_robot_name()
    test_move_to_named_location()
    test_move_to_coordinates_dict()
    test_grasp_and_release_flow()
    test_grasp_while_holding_fails()
    test_release_without_holding_fails()
    test_get_state()
    test_registry_and_factory()

    print("Task13.3 Robot Module tests passed.")


if __name__ == "__main__":

    run_all_tests()
