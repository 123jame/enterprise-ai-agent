"""
Workspace 文件路径解析测试。

运行:
    cd backend
    python -m applications.software_team.tests.test_file_tools
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from applications.software_team.tools.file_tools import ReadFileTool
from applications.software_team.tools.context import workspace_path_ctx
from applications.software_team.tools.workspace_paths import resolve_workspace_file
from app.tools.types import ToolContext


def test_resolve_management_aliases() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        mgmt = root / "management"
        mgmt.mkdir()
        (mgmt / "PROJECT_PLAN.md").write_text("# Plan", encoding="utf-8")
        (mgmt / "TASK_LIST.md").write_text("# Tasks", encoding="utf-8")

        plan = resolve_workspace_file(root, "PROJECT_PLAN.md")
        assert plan is not None
        assert plan.name == "PROJECT_PLAN.md"

        tasks = resolve_workspace_file(root, "management/TASK_LIST.md")
        assert tasks is not None

        missing = resolve_workspace_file(root, "PROGRESS_REPORT.md")
        assert missing is None

        print("resolve_management_aliases: PASS")


def test_read_file_tool_alias() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        mgmt = root / "management"
        mgmt.mkdir()
        (mgmt / "PROJECT_PLAN.md").write_text("# Plan Content", encoding="utf-8")

        token = workspace_path_ctx.set(str(root))

        try:

            tool = ReadFileTool()
            result = tool.execute(
                ToolContext(
                    tool_name="read_file",
                    arguments={"path": "PROJECT_PLAN.md"},
                )
            )

            assert result.success is True
            assert "Plan Content" in result.content
            assert "Resolved path" in result.content

        finally:

            workspace_path_ctx.reset(token)

        print("read_file_tool_alias: PASS")


def main() -> None:

    test_resolve_management_aliases()
    test_read_file_tool_alias()

    print("\n=== File tools path resolution: ALL PASS ===")


if __name__ == "__main__":

    main()
