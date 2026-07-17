from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any


class VerificationCheckType(str, Enum):
    """
    验证检查类型。
    """

    STRUCTURE = "structure"
    IMPORT = "import"
    PYTEST = "pytest"
    LINT = "lint"
    TYPE_CHECK = "type_check"
    EXECUTION = "execution"
    DOCUMENT = "document"


@dataclass
class CheckResult:
    """
    单项验证检查结果。
    """

    check_type: VerificationCheckType

    success: bool

    message: str = ""

    output: str = ""

    skipped: bool = False

    duration_ms: float = 0.0


@dataclass
class VerificationFeedback:
    """
    验证失败反馈，注入 Prompt 供 LLM 修复。
    """

    attempt: int

    agent_name: str

    target: str

    error_log: str

    verification_summary: str

    execution_summary: str

    previous_attempt_summary: str = ""

    def to_shared_context(self) -> dict[str, str]:

        return {
            "verification_attempt": str(self.attempt),
            "verification_error_log": self.error_log,
            "verification_result": self.verification_summary,
            "execution_result": self.execution_summary,
            "previous_attempt": self.previous_attempt_summary,
        }

    @classmethod
    def from_metadata(
        cls,
        metadata: dict[str, Any],
    ) -> VerificationFeedback | None:

        if not metadata.get("verification_retry"):

            return None

        return cls(
            attempt=int(metadata.get("verification_attempt", 1)),
            agent_name=str(metadata.get("team_agent", "")),
            target=str(metadata.get("verification_target", "")),
            error_log=str(metadata.get("verification_error_log", "")),
            verification_summary=str(
                metadata.get("verification_result", "")
            ),
            execution_summary=str(
                metadata.get("execution_result", "")
            ),
            previous_attempt_summary=str(
                metadata.get("previous_attempt", "")
            ),
        )


@dataclass
class VerificationResult:
    """
    验证结果汇总。
    """

    success: bool

    workspace_path: str

    target: str = ""

    checks: list[CheckResult] = field(
        default_factory=list,
    )

    error_log: str = ""

    duration_ms: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    @property
    def summary(self) -> str:
        """
        可读摘要，供 Prompt / Memory 使用。
        """

        lines = [
            f"Target: {self.target or 'workspace'}",
            f"Success: {self.success}",
        ]

        for check in self.checks:

            status = "PASS" if check.success else "FAIL"

            if check.skipped:

                status = "SKIP"

            lines.append(
                f"- [{status}] {check.check_type.value}: {check.message}"
            )

            if not check.success and check.output:

                lines.append(f"  Output: {check.output[:500]}")

        if self.error_log:

            lines.append(f"Error Log:\n{self.error_log[:2000]}")

        return "\n".join(lines)

    @classmethod
    def aggregate(
        cls,
        *,
        workspace_path: str,
        target: str,
        results: list[CheckResult],
    ) -> VerificationResult:

        failed = [
            check
            for check in results
            if not check.success and not check.skipped
        ]

        error_log = "\n".join(
            f"{check.check_type.value}: {check.message}\n{check.output}"
            for check in failed
            if check.output or check.message
        )

        return cls(
            success=len(failed) == 0,
            workspace_path=workspace_path,
            target=target,
            checks=results,
            error_log=error_log.strip(),
            duration_ms=sum(check.duration_ms for check in results),
            metadata={
                "passed": sum(
                    1 for check in results if check.success
                ),
                "failed": len(failed),
                "skipped": sum(
                    1 for check in results if check.skipped
                ),
            },
        )
