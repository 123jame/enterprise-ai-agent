from __future__ import annotations

import shutil
from pathlib import Path

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.execution.command_runner import CommandRunner
from applications.software_team.git.git_context import GitOperationResult


class GitManager:
    """
    统一 Git 操作入口。

    所有 Git 命令经 CommandRunner 执行；
    Agent / Coordinator 禁止直接调用 git CLI。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        command_runner: CommandRunner | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._runner = command_runner or CommandRunner(
            timeout_seconds=self._settings.execution_timeout_seconds,
        )

    def is_available(self) -> bool:

        return shutil.which("git") is not None

    def is_repo(
        self,
        workspace: str | Path,
    ) -> bool:

        git_dir = Path(workspace).resolve() / ".git"

        return git_dir.exists()

    def has_commits(
        self,
        workspace: str | Path,
    ) -> bool:

        result = self._git(
            Path(workspace).resolve(),
            ["rev-parse", "HEAD"],
        )

        return result.success

    def init(
        self,
        workspace: str | Path,
        *,
        initial_branch: str | None = None,
    ) -> GitOperationResult:

        workspace = Path(workspace).resolve()
        branch = initial_branch or self._settings.git_default_branch

        if self.is_repo(workspace):

            return GitOperationResult(
                success=True,
                command="git init (skipped)",
                stdout="Repository already exists.",
                metadata={"already_initialized": True},
            )

        result = self._git(
            workspace,
            ["init", "-b", branch],
        )

        return result

    def status(
        self,
        workspace: str | Path,
    ) -> GitOperationResult:

        return self._git(
            Path(workspace).resolve(),
            ["status", "--porcelain"],
        )

    def add(
        self,
        workspace: str | Path,
        paths: str | list[str] = ".",
    ) -> GitOperationResult:

        workspace = Path(workspace).resolve()

        if isinstance(paths, str):

            args = ["add", paths]

        else:

            args = ["add", *paths]

        return self._git(workspace, args)

    def commit(
        self,
        workspace: str | Path,
        message: str,
    ) -> GitOperationResult:

        return self._git(
            Path(workspace).resolve(),
            ["commit", "-m", message],
        )

    def checkout(
        self,
        workspace: str | Path,
        branch: str,
        *,
        create: bool = False,
    ) -> GitOperationResult:

        args = ["checkout"]

        if create:

            args.append("-b")

        args.append(branch)

        return self._git(
            Path(workspace).resolve(),
            args,
        )

    def branch(
        self,
        workspace: str | Path,
        name: str,
        *,
        create: bool = True,
    ) -> GitOperationResult:

        args = ["branch"]

        if create:

            args.append(name)

        else:

            args.extend(["-d", name])

        return self._git(
            Path(workspace).resolve(),
            args,
        )

    def merge(
        self,
        workspace: str | Path,
        source_branch: str,
        *,
        no_ff: bool = True,
    ) -> GitOperationResult:

        args = ["merge"]

        if no_ff:

            args.append("--no-ff")

        args.extend([source_branch, "-m", f"Merge {source_branch}"])

        return self._git(
            Path(workspace).resolve(),
            args,
        )

    def tag(
        self,
        workspace: str | Path,
        name: str,
        *,
        message: str | None = None,
    ) -> GitOperationResult:

        args = ["tag", name]

        if message:

            args.extend(["-a", name, "-m", message])

        return self._git(
            Path(workspace).resolve(),
            args,
        )

    def current_branch(
        self,
        workspace: str | Path,
    ) -> str:

        result = self._git(
            Path(workspace).resolve(),
            ["rev-parse", "--abbrev-ref", "HEAD"],
        )

        if result.success:

            return result.stdout.strip()

        return ""

    def last_commit_sha(
        self,
        workspace: str | Path,
    ) -> str:

        result = self._git(
            Path(workspace).resolve(),
            ["rev-parse", "HEAD"],
        )

        if result.success:

            return result.stdout.strip()

        return ""

    def last_commit_message(
        self,
        workspace: str | Path,
    ) -> str:

        result = self._git(
            Path(workspace).resolve(),
            ["log", "-1", "--pretty=%s"],
        )

        if result.success:

            return result.stdout.strip()

        return ""

    def log(
        self,
        workspace: str | Path,
        *,
        limit: int = 5,
    ) -> list[str]:

        result = self._git(
            Path(workspace).resolve(),
            [
                "log",
                f"-{limit}",
                "--pretty=format:%h %s (%an)",
            ],
        )

        if not result.success or not result.stdout.strip():

            return []

        return [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

    def diff_stat(
        self,
        workspace: str | Path,
    ) -> str:

        result = self._git(
            Path(workspace).resolve(),
            ["diff", "--stat", "HEAD"],
        )

        if result.stdout.strip():

            return result.stdout.strip()

        status = self.status(workspace)

        return status.stdout.strip()

    def get_conflict_files(
        self,
        workspace: str | Path,
    ) -> list[str]:

        status = self.status(workspace)

        if not status.success:

            return []

        conflicts: list[str] = []

        for line in status.stdout.splitlines():

            if line.startswith(("UU", "AA", "DD")):

                conflicts.append(line[3:].strip())

        return conflicts

    def _git(
        self,
        workspace: Path,
        args: list[str],
    ) -> GitOperationResult:

        if not self.is_available():

            return GitOperationResult(
                success=False,
                command=f"git {' '.join(args)}",
                error_message="git executable not found",
            )

        command = ["git", *args]
        result = self._runner.run(
            command=command,
            cwd=workspace,
        )

        return GitOperationResult(
            success=result.success,
            command=result.command,
            stdout=result.stdout,
            stderr=result.stderr,
            error_message=result.error_message,
            metadata={"exit_code": result.exit_code},
        )
