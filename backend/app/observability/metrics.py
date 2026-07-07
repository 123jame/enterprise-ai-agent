from dataclasses import dataclass
from dataclasses import field

from app.observability.types import LLMEvent
from app.observability.types import PlannerEvent
from app.observability.types import PromptEvent
from app.observability.types import RetrievalEvent
from app.observability.types import ToolEvent
from app.observability.types import TraceEvent
from app.observability.types import TraceEventType


@dataclass
class TraceMetrics:
    """
    一次 Agent 执行的统计指标。
    """

    llm_call_count: int = 0

    tool_call_count: int = 0

    tool_success_count: int = 0

    tool_failure_count: int = 0

    total_duration_ms: float = 0.0

    llm_duration_ms: float = 0.0

    tool_duration_ms: float = 0.0

    plan_step_count: int = 0

    prompt_length: int = 0

    rag_hit_count: int = 0

    @property
    def tool_success_rate(self) -> float:

        if self.tool_call_count == 0:

            return 1.0

        return (
            self.tool_success_count
            / self.tool_call_count
        )

    @property
    def average_llm_duration_ms(self) -> float:

        if self.llm_call_count == 0:

            return 0.0

        return self.llm_duration_ms / self.llm_call_count

    @property
    def average_tool_duration_ms(self) -> float:

        if self.tool_call_count == 0:

            return 0.0

        return self.tool_duration_ms / self.tool_call_count


class MetricsCollector:
    """
    从 TraceEvent 聚合 Metrics。
    """

    def __init__(self):

        self._metrics = TraceMetrics()

    @property
    def metrics(self) -> TraceMetrics:
        return self._metrics

    def reset(self) -> None:

        self._metrics = TraceMetrics()

    def record(self, event: TraceEvent) -> None:

        if isinstance(event, LLMEvent):

            self._metrics.llm_call_count += 1
            self._metrics.llm_duration_ms += event.duration_ms

        elif isinstance(event, ToolEvent):

            self._metrics.tool_call_count += 1
            self._metrics.tool_duration_ms += event.duration_ms

            if event.success:

                self._metrics.tool_success_count += 1

            else:

                self._metrics.tool_failure_count += 1

        elif isinstance(event, PromptEvent):

            self._metrics.prompt_length = max(
                self._metrics.prompt_length,
                event.prompt_length,
            )

        elif isinstance(event, RetrievalEvent):

            self._metrics.rag_hit_count += event.hit_count

        elif isinstance(event, PlannerEvent):

            if event.action in ("plan_created", "plan_complete"):

                self._metrics.plan_step_count = max(
                    self._metrics.plan_step_count,
                    event.step_count,
                )

    def summarize(self) -> dict:

        metrics = self._metrics

        return {
            "llm_call_count": metrics.llm_call_count,
            "tool_call_count": metrics.tool_call_count,
            "tool_success_rate": metrics.tool_success_rate,
            "average_llm_duration_ms": (
                metrics.average_llm_duration_ms
            ),
            "average_tool_duration_ms": (
                metrics.average_tool_duration_ms
            ),
            "plan_step_count": metrics.plan_step_count,
            "prompt_length": metrics.prompt_length,
            "rag_hit_count": metrics.rag_hit_count,
        }
