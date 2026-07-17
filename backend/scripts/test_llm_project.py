"""
模拟 Software Team 项目运行时的 LLM 调用模式。

与 test_llm.py 的区别：
- 注册 5 个 Team Tool
- 模拟 Agent 多轮 Tool 结果累积（项目里最常见、测试脚本最容易漏掉的场景）
- 模拟跨 Agent 的历史消息累积

用法：
    cd backend
    python scripts/test_llm_project.py
"""

from __future__ import annotations

import time

from app.llm.factory import get_llm_client
from app.llm.types import Message
from applications.software_team.tools.registrar import register_team_tools


def _simulate_agent_loop(client, agent: str) -> None:
    """
    模拟单个 Agent 的多轮 Tool Loop：每轮把大段 read_file 结果追加进 messages。
    """

    messages: list[Message] = [
        Message(
            role="system",
            content=(
                f"You are {agent}. Use tools to read and write project files.\n"
                + ("context padding. " * 300)
            ),
        ),
        Message(
            role="user",
            content=(
                "Generate project artifacts. Read docs/Architecture.md and "
                "write code under backend/."
            ),
        ),
    ]

    fake_file = "# Architecture\n" + ("module design line\n" * 1200)

    for round_index in range(1, 5):
        started = time.perf_counter()
        label = f"{agent} loop round {round_index}"

        result = client.chat(messages, use_tools=True)
        elapsed = time.perf_counter() - started

        print(
            f"[OK] {label}: {elapsed:.1f}s, tool_calls={len(result.tool_calls)}"
        )

        if not result.tool_calls:
            break

        tool_calls = result.tool_calls
        messages.append(
            Message(
                role="assistant",
                content=result.content,
                tool_calls=tool_calls,
            )
        )

        for tool_call in tool_calls:
            messages.append(
                Message(
                    role="tool",
                    content=f"[Resolved path: docs/Architecture.md]\n{fake_file}",
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                )
            )


def _simulate_cross_agent_history(client) -> None:
    """
    模拟后续 Agent 继承前面多个 Agent 的历史消息。
    """

    history: list[Message] = []

    for agent in ("ProductAgent", "ArchitectAgent", "BackendAgent"):
        history.extend(
            [
                Message(
                    role="user",
                    content=f"{agent} task instruction",
                ),
                Message(
                    role="assistant",
                    content=(
                        f"{agent} completed output.\n"
                        + ("generated content line\n" * 400)
                    ),
                ),
            ]
        )

    history.append(
        Message(
            role="user",
            content="FrontendAgent: implement UI based on architecture.",
        )
    )

    started = time.perf_counter()
    client.chat(history, use_tools=True)
    elapsed = time.perf_counter() - started
    print(f"[OK] cross-agent history call: {elapsed:.1f}s")


def main() -> None:
    register_team_tools()
    client = get_llm_client()
    tool_count = len(client._get_tool_schemas())

    print(f"Tools registered: {tool_count}")
    print("Simulating project-like multi-turn + history accumulation...")
    print("-" * 60)

    failures: list[str] = []

    for agent in (
        "BackendAgent",
        "FrontendAgent",
    ):
        try:
            _simulate_agent_loop(client, agent)
        except Exception as error:
            failures.append(f"{agent} loop: {error}")
            print(f"[FAIL] {agent} loop: {error}")

    try:
        _simulate_cross_agent_history(client)
    except Exception as error:
        failures.append(f"history: {error}")
        print(f"[FAIL] history: {error}")

    print("-" * 60)

    if failures:
        print("Project-like simulation failed:")
        for item in failures:
            print(f"  - {item}")
        raise SystemExit(1)

    print("Project-like simulation succeeded.")


if __name__ == "__main__":
    main()
