"""
Task13.8 Embodied Demo 测试。

运行:
    cd backend
    python -m applications.embodied_demo.tests.test_embodied_demo
"""

from __future__ import annotations

from app.policy.factory import reset_policy
from app.robot.factory import reset_robot
from applications.embodied_demo.embodied_demo_agent import EmbodiedDemoAgent


def test_demo_full_flow_pick_red_cup() -> None:

    reset_robot()
    reset_policy()

    agent = EmbodiedDemoAgent()
    result = agent.run("帮我拿桌上的红色杯子")

    assert result.success is True
    assert len(result.steps) >= 4

    phases = [step.phase for step in result.steps]

    assert phases[0] == "vision"
    assert "plan" in phases
    assert phases.count("robot") >= 2
    assert result.observations[0].type == "vision"
    assert any(
        observation.type == "robot"
        for observation in result.observations
    )
    assert result.final_robot_state["holding"] == "red cup"
    assert "任务完成" in result.content


def test_demo_empty_instruction() -> None:

    agent = EmbodiedDemoAgent()
    result = agent.run("   ")

    assert result.success is False
    assert result.content == "指令不能为空"


def run_all_tests() -> None:

    test_demo_full_flow_pick_red_cup()
    test_demo_empty_instruction()

    print("Task13.8 Embodied Demo tests passed.")


if __name__ == "__main__":

    run_all_tests()
