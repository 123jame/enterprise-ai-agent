"""
Task13.7 Policy Interface 测试。

运行:
    cd backend
    python -m app.policy.tests.test_policy
"""

from __future__ import annotations

from app.embodied.observation_factory import ObservationFactory
from app.embodied.types import Observation
from app.policy.factory import get_policy
from app.policy.factory import reset_policy
from app.policy.mock import MockPolicy
from app.policy.registry import PolicyProviderRegistry
from app.tools.manager import ToolManager
from app.tools.types import ToolContext


def test_mock_policy_name() -> None:

    policy = MockPolicy()

    assert policy.name == "mock"


def test_predict_from_vision_observation_object() -> None:

    policy = MockPolicy()

    observation = Observation(
        type="vision",
        content="red cup、红色杯子",
        source="analyze_image",
        metadata={
            "detected_objects": ["red cup", "红色杯子"],
        },
    )

    prediction = policy.predict(
        observation,
        "帮我拿桌上的红色杯子",
    )

    assert prediction.observation_type == "vision"
    assert len(prediction.actions) == 2
    assert prediction.actions[0].name == "robot_move"
    assert prediction.actions[0].parameters["target"] == "table"
    assert prediction.actions[1].name == "robot_grasp"
    assert prediction.actions[1].parameters["target"] == "red cup"
    assert prediction.completed is False
    assert prediction.confidence > 0.8


def test_predict_from_robot_grasp_success() -> None:

    policy = MockPolicy()

    prediction = policy.predict(
        {
            "type": "robot",
            "content": "grasp success: red cup",
            "success": True,
        },
        "帮我拿桌上的红色杯子",
    )

    assert prediction.observation_type == "robot"
    assert prediction.completed is True
    assert prediction.actions == []
    assert "任务完成" in prediction.reasoning


def test_predict_from_tool_result_pipeline() -> None:

    tool_result = ToolManager().execute(
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

    prediction = MockPolicy().predict(
        observation,
        "帮我拿桌上的红色杯子",
    )

    assert prediction.actions[1].parameters["target"] == "red cup"


def test_predict_without_observation_suggests_vision() -> None:

    prediction = MockPolicy().predict(
        {
            "type": "generic",
            "content": "",
        },
        "帮我拿桌上的红色杯子",
    )

    assert prediction.actions[0].name == "analyze_image"


def test_registry_and_factory() -> None:

    reset_policy()

    assert "mock" in PolicyProviderRegistry.list_providers()

    policy = get_policy("mock")

    assert isinstance(policy, MockPolicy)

    singleton = get_policy()

    assert singleton is get_policy()


def run_all_tests() -> None:

    test_mock_policy_name()
    test_predict_from_vision_observation_object()
    test_predict_from_robot_grasp_success()
    test_predict_from_tool_result_pipeline()
    test_predict_without_observation_suggests_vision()
    test_registry_and_factory()

    print("Task13.7 Policy Interface tests passed.")


if __name__ == "__main__":

    run_all_tests()
