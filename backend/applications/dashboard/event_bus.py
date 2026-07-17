from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import WebSocket

from applications.dashboard.event_types import DashboardEvent
from applications.dashboard.event_types import DashboardEventType


class EventBus:
    """
    内存事件总线，向 WebSocket 客户端广播实时事件。
    """

    def __init__(self):

        self._connections: set[WebSocket] = set()
        self._history: list[DashboardEvent] = []
        self._max_history = 500

    @property
    def history(self) -> list[DashboardEvent]:

        return list(self._history)

    async def connect(self, websocket: WebSocket) -> None:

        await websocket.accept()
        self._connections.add(websocket)

        if self._history:

            snapshot = {
                "type": "snapshot",
                "events": [event.model_dump() for event in self._history[-50:]],
            }
            await websocket.send_text(json.dumps(snapshot, ensure_ascii=False))

    def disconnect(self, websocket: WebSocket) -> None:

        self._connections.discard(websocket)

    def emit(
        self,
        event_type: DashboardEventType,
        *,
        project_id: str = "",
        session_id: str = "",
        payload: dict[str, Any] | None = None,
    ) -> DashboardEvent:

        event = DashboardEvent(
            type=event_type,
            project_id=project_id,
            session_id=session_id,
            payload=payload or {},
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        self._history.append(event)

        if len(self._history) > self._max_history:

            self._history = self._history[-self._max_history :]

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._broadcast(event))
        except RuntimeError:
            pass

        return event

    async def _broadcast(self, event: DashboardEvent) -> None:

        if not self._connections:

            return

        message = json.dumps(event.model_dump(), ensure_ascii=False)
        stale: list[WebSocket] = []

        for connection in self._connections:

            try:
                await connection.send_text(message)
            except Exception:
                stale.append(connection)

        for connection in stale:

            self._connections.discard(connection)


_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:

    global _event_bus

    if _event_bus is None:

        _event_bus = EventBus()

    return _event_bus
