from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any


class GitEventType(str, Enum):
    """
    Git 事件类型，用于 Memory 记录。
    """

    INIT = "git_init"
    COMMIT = "git_commit"
    BRANCH = "git_branch"
    MERGE = "git_merge"
    TAG = "git_tag"


@dataclass
class GitCommitInfo:
    """
    单次 Git Commit 信息。
    """

    sha: str

    message: str

    branch: str

    agent_name: str = ""

    artifact_ids: list[str] = field(
        default_factory=list,
    )


@dataclass
class GitOperationResult:
    """
    Git 操作通用结果。
    """

    success: bool

    command: str = ""

    stdout: str = ""

    stderr: str = ""

    error_message: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


@dataclass
class MergeResult:
    """
    Merge 操作结果。
    """

    success: bool

    source_branch: str

    target_branch: str

    has_conflicts: bool = False

    conflict_files: list[str] = field(
        default_factory=list,
    )

    message: str = ""

    stdout: str = ""

    stderr: str = ""


@dataclass
class GitContext:
    """
    当前 Workspace 的 Git 状态快照，供 Prompt / Coordinator 使用。
    """

    workspace_path: str

    current_branch: str = ""

    last_commit_sha: str = ""

    last_commit_message: str = ""

    recent_commits: list[str] = field(
        default_factory=list,
    )

    is_initialized: bool = False

    def to_shared_context(self) -> dict[str, str]:

        return {
            "git_current_branch": self.current_branch,
            "git_last_commit_sha": self.last_commit_sha,
            "git_last_commit_message": self.last_commit_message,
            "git_recent_history": "\n".join(self.recent_commits[:5]),
            "git_initialized": str(self.is_initialized),
        }

    def to_prompt_block(self) -> str:

        if not self.is_initialized:

            return "Git repository is not initialized yet."

        history = (
            "\n".join(f"- {line}" for line in self.recent_commits[:5])
            or "(no commits yet)"
        )

        return (
            f"Current Branch: {self.current_branch}\n"
            f"Last Commit: {self.last_commit_sha[:8]} "
            f"{self.last_commit_message}\n"
            f"Recent History:\n{history}"
        )
