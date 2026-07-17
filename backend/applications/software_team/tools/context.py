from __future__ import annotations

from contextvars import ContextVar

workspace_path_ctx: ContextVar[str] = ContextVar(
    "software_team_workspace_path",
    default="",
)
