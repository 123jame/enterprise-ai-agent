from __future__ import annotations

from pathlib import Path
from typing import Any

from app.tools.base_tool import BaseTool
from app.tools.types import ToolContext
from app.tools.types import ToolResult

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.tools.context import workspace_path_ctx


class SearchFilesTool(BaseTool):
    """
    在 Workspace 内搜索文本。
    """

    @property
    def name(self) -> str:

        return "search_files"

    @property
    def description(self) -> str:

        return (
            "Search for a keyword in text files under the project "
            "workspace and return matching file paths and snippets."
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
                        "query": {
                            "type": "string",
                            "description": "Keyword to search for.",
                        },
                        "directory": {
                            "type": "string",
                            "description": (
                                "Relative directory to search, default '.'"
                            ),
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    def execute(
        self,
        context: ToolContext,
    ) -> ToolResult:

        try:

            query = context.arguments.get("query", "").strip()
            directory = context.arguments.get(
                "directory",
                ".",
            )

            if not query:

                return ToolResult(
                    success=False,
                    content="Query is required.",
                )

            workspace = Path(workspace_path_ctx.get())

            if not workspace:

                return ToolResult(
                    success=False,
                    content="Workspace path is not set.",
                )

            root = (workspace / directory).resolve()

            if not root.exists():

                return ToolResult(
                    success=False,
                    content=f"Directory not found: {directory}",
                )

            matches: list[str] = []

            for file_path in sorted(root.rglob("*")):

                if not file_path.is_file():

                    continue

                try:

                    text = file_path.read_text(
                        encoding=DEFAULT_ENCODING,
                    )

                except OSError:

                    continue

                if query.lower() not in text.lower():

                    continue

                relative = file_path.relative_to(workspace)
                snippet = text[:300].replace("\n", " ")

                matches.append(
                    f"{relative}: {snippet}"
                )

            if not matches:

                return ToolResult(
                    success=True,
                    content=f"No matches for '{query}'",
                )

            return ToolResult(
                success=True,
                content="\n".join(matches[:20]),
            )

        except Exception as error:

            return ToolResult(
                success=False,
                content=str(error),
            )
