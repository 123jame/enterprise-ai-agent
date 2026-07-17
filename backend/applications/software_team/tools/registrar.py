from __future__ import annotations

from app.tools.registry import ToolRegistry

from applications.software_team.tools.file_tools import ListFilesTool
from applications.software_team.tools.file_tools import ReadFileTool
from applications.software_team.tools.file_tools import WriteFileTool
from applications.software_team.tools.git_tool import GitTool
from applications.software_team.tools.search_tool import SearchFilesTool

_REGISTERED = False


def register_team_tools() -> None:
    """
    注册 Software Team 专用 Tool 到 Framework ToolRegistry。

    幂等调用；Workspace 路径通过 contextvars 在运行时注入。
    """

    global _REGISTERED

    if _REGISTERED:

        return

    for tool in (
        ReadFileTool(),
        WriteFileTool(),
        ListFilesTool(),
        SearchFilesTool(),
        GitTool(),
    ):

        ToolRegistry.register(tool)

    _REGISTERED = True
