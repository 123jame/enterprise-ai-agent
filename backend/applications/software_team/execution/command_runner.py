from __future__ import annotations

import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from applications.software_team.config.defaults import DEFAULT_ENCODING


@dataclass(frozen=True)
class CommandRunResult:
    """
    底层命令执行结果。
    """

    success: bool

    command: str

    exit_code: int

    stdout: str

    stderr: str

    duration_ms: float

    error_message: str = ""


class CommandRunner:
    """
    Software Team 唯一允许使用 subprocess 的组件。

    Agent / Coordinator 禁止直接运行系统命令。
    """

    def __init__(
        self,
        timeout_seconds: int = 120,
    ):

        self._timeout_seconds = timeout_seconds

    @staticmethod
    def _resolve_command(
        command: list[str],
    ) -> list[str]:

        if not command:

            return command

        executable = command[0]

        if sys.platform == "win32" and executable in {
            "npm",
            "npx",
            "node",
        }:

            resolved = shutil.which(executable)

            if resolved:

                return [resolved, *command[1:]]

        return command

    def run(
        self,
        *,
        command: list[str],
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> CommandRunResult:

        cwd = cwd.resolve()
        resolved_command = self._resolve_command(command)
        command_display = " ".join(resolved_command)
        start = time.perf_counter()

        try:

            completed = subprocess.run(
                resolved_command,
                cwd=str(cwd),
                env=env,
                capture_output=True,
                text=True,
                encoding=DEFAULT_ENCODING,
                errors="replace",
                timeout=self._timeout_seconds,
                check=False,
            )

            duration_ms = (time.perf_counter() - start) * 1000

            success = completed.returncode == 0

            return CommandRunResult(
                success=success,
                command=command_display,
                exit_code=completed.returncode,
                stdout=completed.stdout or "",
                stderr=completed.stderr or "",
                duration_ms=duration_ms,
                error_message=(
                    ""
                    if success
                    else (
                        completed.stderr.strip()
                        or f"Command failed: {command_display}"
                    )
                ),
            )

        except subprocess.TimeoutExpired as error:

            duration_ms = (time.perf_counter() - start) * 1000

            return CommandRunResult(
                success=False,
                command=command_display,
                exit_code=-1,
                stdout=error.stdout or "",
                stderr=error.stderr or "",
                duration_ms=duration_ms,
                error_message=(
                    f"Command timed out after "
                    f"{self._timeout_seconds}s: {command_display}"
                ),
            )

        except FileNotFoundError as error:

            duration_ms = (time.perf_counter() - start) * 1000

            return CommandRunResult(
                success=False,
                command=command_display,
                exit_code=-1,
                stdout="",
                stderr=str(error),
                duration_ms=duration_ms,
                error_message=str(error),
            )

        except OSError as error:

            duration_ms = (time.perf_counter() - start) * 1000

            return CommandRunResult(
                success=False,
                command=command_display,
                exit_code=-1,
                stdout="",
                stderr=str(error),
                duration_ms=duration_ms,
                error_message=str(error),
            )
