from __future__ import annotations

from pathlib import Path
from typing import Any

from app.tools.base_tool import BaseTool
from app.tools.types import ToolContext
from app.tools.types import ToolResult

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.defaults import MAX_PRD_WRITE_CHARS
from applications.software_team.config.defaults import MAX_TOOL_FILE_CHARS
from applications.software_team.tools.context import workspace_path_ctx
from applications.software_team.tools.workspace_paths import build_not_found_message
from applications.software_team.tools.workspace_paths import resolve_workspace_file


def _truncate_tool_content(content: str, limit: int = MAX_TOOL_FILE_CHARS) -> str:

    if len(content) <= limit:

        return content

    return (
        f"{content[:limit]}\n\n"
        f"...[truncated {len(content) - limit} chars to protect LLM request size]"
    )


def _resolve_workspace_path(relative_path: str) -> Path:
    """
    将相对路径解析到当前 Project Workspace 内，防止路径穿越。
    """

    workspace = Path(workspace_path_ctx.get())

    if not workspace:

        raise ValueError(
            "Workspace path is not set for team tools."
        )

    target = (workspace / relative_path).resolve()
    workspace_resolved = workspace.resolve()

    if (
        target != workspace_resolved
        and workspace_resolved not in target.parents
    ):

        raise ValueError(
            f"Path escapes workspace: {relative_path}"
        )

    return target


class ReadFileTool(BaseTool):
    """
    读取 Workspace 内文件内容。
    """

    @property
    def name(self) -> str:

        return "read_file"

    @property
    def description(self) -> str:

        return (
            "Read a text file from the project workspace. "
            "Path must be relative to workspace root. "
            "Management reports live under management/, e.g. "
            "management/PROJECT_PLAN.md."
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
                        "path": {
                            "type": "string",
                            "description": (
                                "Relative file path, e.g. docs/PRD.md or "
                                "management/PROJECT_PLAN.md"
                            ),
                        },
                    },
                    "required": ["path"],
                },
            },
        }

    def execute(
        self,
        context: ToolContext,
    ) -> ToolResult:

        try:

            path = context.arguments.get("path", "")
            workspace = Path(workspace_path_ctx.get())

            if not workspace:

                raise ValueError(
                    "Workspace path is not set for team tools."
                )

            file_path = resolve_workspace_file(workspace, path)

            if file_path is None:

                return ToolResult(
                    success=False,
                    content=build_not_found_message(path),
                )

            content = file_path.read_text(
                encoding=DEFAULT_ENCODING,
            )

            resolved = file_path.relative_to(workspace.resolve())
            prefix = (
                f"[Resolved path: {resolved.as_posix()}]\n"
                if resolved.as_posix() != path.replace("\\", "/").lstrip("./")
                else ""
            )

            return ToolResult(
                success=True,
                content=f"{prefix}{_truncate_tool_content(content)}",
            )

        except Exception as error:

            return ToolResult(
                success=False,
                content=str(error),
            )


class WriteFileTool(BaseTool):
    """
    写入 Workspace 内文件。
    """

    @property
    def name(self) -> str:

        return "write_file"

    @property
    def description(self) -> str:

        return (
            "Write content to a file in the project workspace. "
            "Creates parent directories if needed."
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
                        "path": {
                            "type": "string",
                            "description": (
                                "Relative file path, e.g. docs/PRD.md"
                            ),
                        },
                        "content": {
                            "type": "string",
                            "description": "File content to write.",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
        }

    def execute(
        self,
        context: ToolContext,
    ) -> ToolResult:

        try:

            path = context.arguments.get("path", "")
            content = context.arguments.get("content", "")
            normalized = str(path).replace("\\", "/").lstrip("./")
            truncated_note = ""

            if normalized.endswith("docs/PRD.md") and len(content) > MAX_PRD_WRITE_CHARS:

                truncated_note = (
                    f" [PRD truncated to {MAX_PRD_WRITE_CHARS} chars "
                    f"from {len(content)}]"
                )
                content = content[:MAX_PRD_WRITE_CHARS]

            file_path = _resolve_workspace_path(path)

            file_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            file_path.write_text(
                content,
                encoding=DEFAULT_ENCODING,
            )

            return ToolResult(
                success=True,
                content=f"Written {path} ({len(content)} chars){truncated_note}",
            )

        except Exception as error:

            return ToolResult(
                success=False,
                content=str(error),
            )


class ListFilesTool(BaseTool):
    """
    列出 Workspace 内文件。
    """

    @property
    def name(self) -> str:

        return "list_files"

    @property
    def description(self) -> str:

        return (
            "List files under a directory in the project workspace."
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
                        "directory": {
                            "type": "string",
                            "description": (
                                "Relative directory path, default '.'"
                            ),
                        },
                    },
                },
            },
        }

    def execute(
        self,
        context: ToolContext,
    ) -> ToolResult:

        try:

            directory = context.arguments.get(
                "directory",
                ".",
            )

            dir_path = _resolve_workspace_path(directory)

            if not dir_path.exists():

                return ToolResult(
                    success=False,
                    content=f"Directory not found: {directory}",
                )

            files = sorted(
                str(path.relative_to(dir_path))
                for path in dir_path.rglob("*")
                if path.is_file()
            )

            if not files:

                return ToolResult(
                    success=True,
                    content=f"[{directory}] (empty)",
                )

            return ToolResult(
                success=True,
                content="\n".join(files),
            )

        except Exception as error:

            return ToolResult(
                success=False,
                content=str(error),
            )
