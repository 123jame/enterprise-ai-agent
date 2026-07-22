"""
Task13.8 具身智能 Demo 入口。

用法:
    cd backend
    python -m applications.embodied_demo.demo
    python -m applications.embodied_demo.demo --instruction "帮我拿桌上的红色杯子"
"""

from __future__ import annotations

import argparse

from applications.embodied_demo.embodied_demo_agent import EmbodiedDemoAgent


def main() -> None:

    parser = argparse.ArgumentParser(
        description="Embodied AI Agent Demo",
    )

    parser.add_argument(
        "--instruction",
        default="帮我拿桌上的红色杯子",
        help="用户任务指令",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Embodied AI Agent Demo")
    print("=" * 60)
    print(f"User: {args.instruction}")
    print("=" * 60)

    agent = EmbodiedDemoAgent()
    result = agent.run(args.instruction)

    for index, step in enumerate(result.steps, start=1):

        print(f"\n[Step {index}] {step.phase.upper()} - {step.description}")

        if step.tool_name:

            print(f"  Tool: {step.tool_name}")
            print(f"  Args: {step.tool_arguments}")

        if step.observation:

            print(
                f"  Observation: "
                f"type={step.observation.type}, "
                f"content={step.observation.content}"
            )

        if step.policy_prediction:

            print(f"  Policy: {step.policy_prediction.reasoning}")

            if step.policy_prediction.actions:

                action_names = [
                    action.name
                    for action in step.policy_prediction.actions
                ]

                print(f"  Planned Actions: {action_names}")

        if step.detail:

            print(f"  Detail: {step.detail}")

    print("\n" + "=" * 60)
    print(f"Success: {result.success}")
    print(f"Result: {result.content}")

    if result.final_robot_state:

        print(f"Robot State: {result.final_robot_state}")

    print("=" * 60)


if __name__ == "__main__":

    main()
