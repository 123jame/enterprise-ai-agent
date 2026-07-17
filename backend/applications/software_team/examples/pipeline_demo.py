"""
P4 Multi-Agent Collaboration — 端到端流水线 Demo。

运行方式（在 backend 目录下）:

    python -m applications.software_team.examples.pipeline_demo
"""

from __future__ import annotations

from uuid import uuid4

from applications.software_team.coordinator.coordinator import (
    SoftwareTeamCoordinator,
)


def main() -> None:

    print("=" * 60)
    print("P4 Software Team Pipeline Demo")
    print("=" * 60)

    coordinator = SoftwareTeamCoordinator()

    result = coordinator.run(
        session_id=f"demo_{uuid4().hex[:8]}",
        user_requirement="开发一个图书管理系统",
        project_name="Library Management System",
    )

    print("\n--- 执行结果 ---")
    print(f"Success: {result.success}")
    print(f"Status: {result.project.status.value}")
    print(f"Workspace: {result.project.workspace_path}")
    print(f"Artifact Count: {len(result.artifacts)}")
    print("\n--- 产物列表 ---")

    for artifact in result.artifacts:

        print(f"  [{artifact.owner}] {artifact.name} ({artifact.type})")

    print("\n--- 输出摘要 ---")
    print(result.content)

    if not result.success:

        raise SystemExit(1)

    print("\nDemo Finished.")


if __name__ == "__main__":

    main()
