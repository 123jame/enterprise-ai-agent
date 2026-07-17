from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any


class ProjectType(str, Enum):
    """
    Workspace 内可识别的项目类型。
    """

    FASTAPI = "fastapi"
    PYTHON = "python"
    REACT = "react"
    VUE = "vue"
    STATIC = "static"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DetectedProject:
    """
    检测到的可执行子项目。
    """

    project_type: ProjectType

    root_path: str

    name: str

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


@dataclass
class ExecutionResult:
    """
    单次或聚合执行结果。

    ExecutionManager.execute() 的统一返回类型。
    """

    success: bool

    workspace_path: str

    project_type: ProjectType = ProjectType.UNKNOWN

    target: str = ""

    command: str = ""

    exit_code: int = 0

    stdout: str = ""

    stderr: str = ""

    duration_ms: float = 0.0

    error_message: str = ""

    sub_results: list[ExecutionResult] = field(
        default_factory=list,
    )

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    @property
    def combined_output(self) -> str:
        """
        合并 stdout / stderr，便于注入 Prompt。
        """

        parts: list[str] = []

        if self.stdout:

            parts.append(self.stdout)

        if self.stderr:

            parts.append(self.stderr)

        for sub in self.sub_results:

            parts.append(sub.combined_output)

        return "\n".join(
            part.strip()
            for part in parts
            if part.strip()
        )

    @classmethod
    def aggregate(
        cls,
        *,
        workspace_path: str,
        results: list[ExecutionResult],
    ) -> ExecutionResult:
        """
        将多个子项目执行结果聚合为一个 ExecutionResult。
        """

        if not results:

            return cls(
                success=True,
                workspace_path=workspace_path,
                metadata={"message": "No runnable projects detected."},
            )

        success = all(result.success for result in results)

        return cls(
            success=success,
            workspace_path=workspace_path,
            project_type=results[0].project_type,
            target="aggregate",
            exit_code=max(result.exit_code for result in results),
            stdout="\n".join(
                result.stdout
                for result in results
                if result.stdout
            ),
            stderr="\n".join(
                result.stderr
                for result in results
                if result.stderr
            ),
            duration_ms=sum(
                result.duration_ms for result in results
            ),
            error_message="; ".join(
                result.error_message
                for result in results
                if result.error_message
            ),
            sub_results=results,
            metadata={
                "executed_count": len(results),
                "failed_count": sum(
                    1 for result in results if not result.success
                ),
            },
        )
