from __future__ import annotations

from typing import Any

from applications.dashboard.event_bus import get_event_bus
from applications.dashboard.event_types import DashboardEventType
from applications.dashboard.state_store import get_state_store


class DashboardEventListener:
    """
    Coordinator / Pipeline 事件监听器，广播至 WebSocket。
    """

    def __init__(
        self,
        *,
        project_id: str,
        session_id: str,
    ):

        self._project_id = project_id
        self._session_id = session_id
        self._bus = get_event_bus()
        self._store = get_state_store()

    def on_project_started(self, name: str, requirement: str) -> None:

        self._store.create_project(
            project_id=self._project_id,
            session_id=self._session_id,
            name=name,
            requirement=requirement,
        )
        self._bus.emit(
            DashboardEventType.PROJECT_STARTED,
            project_id=self._project_id,
            session_id=self._session_id,
            payload={"name": name, "requirement": requirement},
        )

    def on_workflow_status(self, stage: str, status: str, detail: str = "") -> None:

        self._store.set_stage(
            self._project_id,
            stage,
            status=status,
            detail=detail,
        )
        self._bus.emit(
            DashboardEventType.WORKFLOW_STATUS,
            project_id=self._project_id,
            session_id=self._session_id,
            payload={"stage": stage, "status": status, "detail": detail},
        )

    def on_agent_started(self, agent_name: str, task: str = "") -> None:

        self._store.mark_agent_started(
            self._project_id,
            agent_name,
            task=task,
        )
        self._bus.emit(
            DashboardEventType.AGENT_STARTED,
            project_id=self._project_id,
            session_id=self._session_id,
            payload={"agent": agent_name, "task": task},
        )

    def on_agent_finished(
        self,
        agent_name: str,
        *,
        success: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:

        meta = metadata or {}
        self._store.mark_agent_finished(
            self._project_id,
            agent_name,
            success=success,
            execution_time_ms=float(meta.get("execution_time_ms", 0)),
            token_usage=int(meta.get("token_usage", 0)),
            tool_calls=int(meta.get("tool_calls", 0)),
        )
        self._bus.emit(
            DashboardEventType.AGENT_FINISHED,
            project_id=self._project_id,
            session_id=self._session_id,
            payload={"agent": agent_name, "success": success, **meta},
        )
        self._bus.emit(
            DashboardEventType.TASK_FINISHED,
            project_id=self._project_id,
            session_id=self._session_id,
            payload={"agent": agent_name, "success": success},
        )

    def on_git_update(self, entry: dict[str, Any]) -> None:

        self._store.update_git_log(self._project_id, entry)
        self._bus.emit(
            DashboardEventType.GIT_UPDATE,
            project_id=self._project_id,
            session_id=self._session_id,
            payload=entry,
        )

    def on_deployment_finished(self, log: dict[str, Any]) -> None:

        self._store.update_deployment(self._project_id, log)
        self._bus.emit(
            DashboardEventType.DEPLOYMENT_FINISHED,
            project_id=self._project_id,
            session_id=self._session_id,
            payload=log,
        )

        if log.get("version"):

            self._bus.emit(
                DashboardEventType.RELEASE_FINISHED,
                project_id=self._project_id,
                session_id=self._session_id,
                payload={
                    "version": log.get("version"),
                    "deploy_url": log.get("deploy_url", ""),
                },
            )

    def on_operation_update(self, log: dict[str, Any]) -> None:

        self._store.update_operations(self._project_id, log)
        self._bus.emit(
            DashboardEventType.OPERATION_UPDATE,
            project_id=self._project_id,
            session_id=self._session_id,
            payload=log,
        )

    def on_project_finished(
        self,
        *,
        success: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:

        self._store.finish_project(
            self._project_id,
            success=success,
            metadata=metadata,
        )
        self._bus.emit(
            DashboardEventType.PROJECT_FINISHED,
            project_id=self._project_id,
            session_id=self._session_id,
            payload={"success": success, **(metadata or {})},
        )

    def on_log(self, message: str) -> None:

        state = self._store.get(self._project_id)

        if state is not None:

            state.append_log(message)

        self._bus.emit(
            DashboardEventType.LOG,
            project_id=self._project_id,
            session_id=self._session_id,
            payload={"message": message},
        )
