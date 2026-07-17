from __future__ import annotations

from typing import Any

from app.tools.base_tool import BaseTool
from app.tools.types import ToolContext
from app.tools.types import ToolResult

from applications.software_team.git.git_manager import GitManager
from applications.software_team.tools.context import workspace_path_ctx


class GitTool(BaseTool):
    """
    Git 只读 Tool：委托 GitManager，供 Agent Loop 查询状态。

    Agent 不得通过本 Tool 执行 commit/merge，由 GitService 统一调度。
    """

    _READONLY_ACTIONS = frozenset({
        "status",
        "log",
        "branch",
    })

    def __init__(
        self,
        git_manager: GitManager | None = None,
    ):

        self._git = git_manager or GitManager()

    @property
    def name(self) -> str:

        return "git"

    @property
    def description(self) -> str:

        return (
            "Read-only Git queries: status, log, branch. "
            "Write operations are handled by the pipeline."
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
                        "action": {
                            "type": "string",
                            "enum": list(self._READONLY_ACTIONS),
                            "description": "Git read action.",
                        },
                    },
                    "required": ["action"],
                },
            },
        }

    def execute(
        self,
        context: ToolContext,
    ) -> ToolResult:

        action = context.arguments.get("action", "status")
        workspace = workspace_path_ctx.get()

        if not workspace:

            return ToolResult(
                success=False,
                content="Workspace path is not set.",
            )

        if action not in self._READONLY_ACTIONS:

            return ToolResult(
                success=False,
                content=(
                    f"Action '{action}' not allowed via Tool. "
                    "Commits are handled by GitService."
                ),
            )

        if action == "status":

            result = self._git.status(workspace)

            return ToolResult(
                success=result.success,
                content=result.stdout or result.error_message,
            )

        if action == "log":

            lines = self._git.log(workspace, limit=5)

            return ToolResult(
                success=True,
                content="\n".join(lines) or "(empty log)",
            )

        branch = self._git.current_branch(workspace)

        return ToolResult(
            success=True,
            content=branch or "unknown",
        )
