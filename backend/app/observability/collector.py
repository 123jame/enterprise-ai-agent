import time
from typing import TYPE_CHECKING
from uuid import uuid4

from app.observability.types import Trace
from app.observability.types import TraceEvent

if TYPE_CHECKING:
    from app.observability.exporter import TraceExporter
    from app.observability.metrics import MetricsCollector


class TraceCollector:
    """
    Trace 收集器。

    负责收集 TraceEvent，ChatAgent 不直接写日志。
    与 AgentTracer 配合：Tracer 转发事件，Collector 统一存储。
    """

    def __init__(
        self,
        exporter: "TraceExporter | None" = None,
        metrics_collector: "MetricsCollector | None" = None,
    ):

        self._exporter = exporter
        self._metrics_collector = metrics_collector
        self._current_trace: Trace | None = None

    @property
    def current_trace(self) -> Trace | None:
        return self._current_trace

    def start_trace(
        self,
        session_id: str,
        metadata: dict | None = None,
    ) -> Trace:

        trace = Trace(
            trace_id=uuid4().hex,
            session_id=session_id,
            start_time=time.time(),
            metadata=metadata or {},
        )

        self._current_trace = trace

        return trace

    def record(self, event: TraceEvent) -> None:

        if self._metrics_collector is not None:

            self._metrics_collector.record(event)

        if self._current_trace is None:

            return

        self._current_trace.events.append(event)

    def finish_trace(self) -> Trace | None:

        if self._current_trace is None:

            return None

        end_time = time.time()

        self._current_trace.end_time = end_time
        self._current_trace.duration = (
            end_time - self._current_trace.start_time
        )

        trace = self._current_trace

        if self._exporter is not None:

            self._exporter.export(trace)

        self._current_trace = None

        return trace
