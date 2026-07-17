from __future__ import annotations

from dataclasses import dataclass

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.execution.execution_result import ExecutionResult
from applications.software_team.execution.verification_result import VerificationFeedback
from applications.software_team.execution.verification_result import VerificationResult


@dataclass(frozen=True)
class RetryDecision:
    """
    重试决策结果。
    """

    should_retry: bool

    attempt: int

    max_retries: int

    reason: str = ""


class RetryPolicy:
    """
    验证失败后的重试策略。

    默认最多重试 3 次（不含首次生成）。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        max_retries: int | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._max_retries = (
            max_retries
            if max_retries is not None
            else self._settings.max_verification_retries
        )

    @property
    def max_retries(self) -> int:

        return self._max_retries

    def evaluate(
        self,
        *,
        attempt: int,
        verification: VerificationResult,
        execution: ExecutionResult | None = None,
    ) -> RetryDecision:
        """
        判断是否应继续重试。

        attempt: 当前是第几次修复尝试（从 1 开始）。
        """

        if verification.success:

            if execution is not None and not execution.success:

                if attempt >= self._max_retries:

                    return RetryDecision(
                        should_retry=False,
                        attempt=attempt,
                        max_retries=self._max_retries,
                        reason="Execution failed, max retries reached",
                    )

                return RetryDecision(
                    should_retry=True,
                    attempt=attempt,
                    max_retries=self._max_retries,
                    reason="Execution failed",
                )

            return RetryDecision(
                should_retry=False,
                attempt=attempt,
                max_retries=self._max_retries,
                reason="Verification passed",
            )

        if attempt >= self._max_retries:

            return RetryDecision(
                should_retry=False,
                attempt=attempt,
                max_retries=self._max_retries,
                reason="Verification failed, max retries reached",
            )

        return RetryDecision(
            should_retry=True,
            attempt=attempt,
            max_retries=self._max_retries,
            reason="Verification failed",
        )

    def build_feedback(
        self,
        *,
        agent_name: str,
        target: str,
        attempt: int,
        verification: VerificationResult,
        execution: ExecutionResult | None = None,
        previous_summary: str = "",
    ) -> VerificationFeedback:

        return VerificationFeedback(
            attempt=attempt,
            agent_name=agent_name,
            target=target,
            error_log=verification.error_log,
            verification_summary=verification.summary,
            execution_summary=(
                execution.combined_output[:2000]
                if execution is not None
                else ""
            ),
            previous_attempt_summary=previous_summary,
        )

    def build_fix_instruction(
        self,
        feedback: VerificationFeedback,
    ) -> str:
        """
        生成修复任务指令，供 Agent Loop 使用。
        """

        return (
            f"第 {feedback.attempt} 次修复尝试。"
            f"上次验证未通过，请根据以下信息修复 {feedback.target} 相关代码。\n\n"
            f"## Verification Result\n{feedback.verification_summary}\n\n"
            f"## Execution Output\n{feedback.execution_summary}\n\n"
            f"## Error Log\n{feedback.error_log}\n\n"
            f"## Previous Attempt\n{feedback.previous_attempt_summary}\n\n"
            "请使用 write_file 工具修正文件，确保通过结构与运行验证。"
        )
