from dataclasses import asdict
from typing import Any

from app.observability.types import Trace
from app.observability.types import TraceEvent


def event_to_dict(event: TraceEvent) -> dict[str, Any]:

    payload = asdict(event)
    payload["event_type"] = event.event_type.value

    return payload


def trace_to_dict(trace: Trace) -> dict[str, Any]:

    return {
        "trace_id": trace.trace_id,
        "session_id": trace.session_id,
        "start_time": trace.start_time,
        "end_time": trace.end_time,
        "duration": trace.duration,
        "metadata": trace.metadata,
        "events": [
            event_to_dict(event)
            for event in trace.events
        ],
    }
