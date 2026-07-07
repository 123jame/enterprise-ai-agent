from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field

from app.observability.types import LLMEvent
from app.observability.types import ToolEvent
from app.observability.types import Trace
from app.observability.types import TraceEventType


@dataclass
class EvaluationResult:
    """
    评测结果。
    """

    passed: bool

    score: float

    checks: dict[str, bool] = field(
        default_factory=dict
    )

    message: str = ""


class Evaluator(ABC):
    """
    Trace 评测器抽象。

    预留 LLM Judge、Benchmark、A/B Testing。
    """

    @abstractmethod
    def evaluate(self, trace: Trace) -> EvaluationResult:
        pass


class RuleBasedEvaluator(Evaluator):
    """
    基于规则的默认评测器。
    """

    def evaluate(self, trace: Trace) -> EvaluationResult:

        checks: dict[str, bool] = {}

        checks["has_events"] = len(trace.events) > 0

        checks["has_prompt"] = any(
            event.event_type == TraceEventType.PROMPT
            for event in trace.events
        )

        llm_events = [
            event
            for event in trace.events
            if isinstance(event, LLMEvent)
        ]

        checks["has_llm_response"] = any(
            not event.error
            for event in llm_events
        )

        tool_events = [
            event
            for event in trace.events
            if isinstance(event, ToolEvent)
        ]

        if tool_events:

            checks["all_tools_succeeded"] = all(
                event.success
                for event in tool_events
            )

        else:

            checks["all_tools_succeeded"] = True

        checks["completed_in_time"] = (
            trace.duration is not None
            and trace.duration >= 0
        )

        passed = all(checks.values())
        score = sum(checks.values()) / len(checks)

        message = (
            "All checks passed."
            if passed
            else "Some checks failed: "
            + ", ".join(
                name
                for name, ok in checks.items()
                if not ok
            )
        )

        return EvaluationResult(
            passed=passed,
            score=score,
            checks=checks,
            message=message,
        )


class LLMJudgeEvaluator(Evaluator):
    """
    LLM Judge 评测器（预留）。
    """

    def evaluate(self, trace: Trace) -> EvaluationResult:

        return EvaluationResult(
            passed=True,
            score=0.0,
            message="LLMJudgeEvaluator is not implemented yet.",
        )
