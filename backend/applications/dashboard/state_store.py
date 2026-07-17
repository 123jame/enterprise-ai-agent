from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any

from applications.dashboard.event_types import AGENT_STAGE_MAP
from applications.dashboard.event_types import WORKFLOW_STAGES


@dataclass
class AgentRuntimeState:
    """
    Agent 运行时状态（Dashboard 只读视图）。
    """

    name: str
    status: str = "idle"
    current_task: str = ""
    token_usage: int = 0
    execution_time_ms: float = 0.0
    tool_calls: int = 0
    workload: float = 0.0
    stage: str = ""
    started_at: str = ""
    finished_at: str = ""


@dataclass
class WorkflowStageState:
    """
    工作流阶段状态。
    """

    id: str
    label: str
    status: str = "pending"
    started_at: str = ""
    finished_at: str = ""
    detail: str = ""


@dataclass
class ProjectRuntimeState:
    """
    项目运行时状态。
    """

    project_id: str
    session_id: str
    name: str
    requirement: str
    status: str = "created"
    current_stage: str = "requirement"
    started_at: str = ""
    finished_at: str = ""
    agents: dict[str, AgentRuntimeState] = field(default_factory=dict)
    workflow_stages: list[WorkflowStageState] = field(default_factory=list)
    git_log: list[dict[str, Any]] = field(default_factory=list)
    deployment_log: dict[str, Any] = field(default_factory=dict)
    operations_log: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:

        if not self.workflow_stages:

            self.workflow_stages = _default_stages()

    def append_log(self, message: str) -> None:

        timestamp = datetime.utcnow().isoformat() + "Z"
        self.logs.append(f"[{timestamp}] {message}")

        if len(self.logs) > 200:

            self.logs = self.logs[-200:]


def _default_stages() -> list[WorkflowStageState]:

    labels = {
        "requirement": "Requirement",
        "planning": "Planning",
        "architecture": "Architecture",
        "development": "Development",
        "verification": "Verification",
        "git": "Git",
        "deployment": "Deployment",
        "operations": "Operations",
        "knowledge": "Knowledge",
        "completed": "Completed",
    }

    return [
        WorkflowStageState(id=stage_id, label=labels[stage_id])
        for stage_id in WORKFLOW_STAGES
    ]


class DashboardStateStore:
    """
    Dashboard 内存状态存储。
    """

    _STAGE_LABELS = {
        "requirement": "Requirement",
        "planning": "Planning",
        "architecture": "Architecture",
        "development": "Development",
        "verification": "Verification",
        "git": "Git",
        "deployment": "Deployment",
        "operations": "Operations",
        "knowledge": "Knowledge",
        "completed": "Completed",
    }

    def __init__(self):

        self._projects: dict[str, ProjectRuntimeState] = {}
        self._session_index: dict[str, str] = {}

    def create_project(
        self,
        *,
        project_id: str,
        session_id: str,
        name: str,
        requirement: str,
    ) -> ProjectRuntimeState:

        state = ProjectRuntimeState(
            project_id=project_id,
            session_id=session_id,
            name=name,
            requirement=requirement,
            status="running",
            current_stage="requirement",
            started_at=datetime.utcnow().isoformat() + "Z",
        )
        state.workflow_stages[0].status = "active"
        state.append_log(f"Project started: {name}")

        self._projects[project_id] = state
        self._session_index[session_id] = project_id

        return state

    def get(self, project_id: str) -> ProjectRuntimeState | None:

        return self._projects.get(project_id)

    def get_by_session(self, session_id: str) -> ProjectRuntimeState | None:

        project_id = self._session_index.get(session_id)

        if project_id is None:

            return None

        return self._projects.get(project_id)

    def migrate_project_id(
        self,
        old_id: str,
        new_id: str,
    ) -> None:

        if not old_id or not new_id or old_id == new_id:

            return

        state = self._projects.pop(old_id, None)

        if state is None:

            return

        state.project_id = new_id
        self._projects[new_id] = state
        self._session_index[state.session_id] = new_id

    def list_projects(self) -> list[ProjectRuntimeState]:

        return sorted(
            self._projects.values(),
            key=lambda item: item.started_at,
            reverse=True,
        )

    def set_stage(
        self,
        project_id: str,
        stage_id: str,
        *,
        status: str = "active",
        detail: str = "",
    ) -> None:

        state = self._projects.get(project_id)

        if state is None:

            return

        state.current_stage = stage_id

        for stage in state.workflow_stages:

            if stage.id == stage_id:

                stage.status = status

                if status == "active" and not stage.started_at:

                    stage.started_at = datetime.utcnow().isoformat() + "Z"

                if status in {"completed", "failed"}:

                    stage.finished_at = datetime.utcnow().isoformat() + "Z"

                if detail:

                    stage.detail = detail

            elif stage.status == "active" and stage.id != stage_id:

                stage.status = "completed"
                stage.finished_at = datetime.utcnow().isoformat() + "Z"

    def mark_agent_started(
        self,
        project_id: str,
        agent_name: str,
        task: str = "",
    ) -> None:

        state = self._projects.get(project_id)

        if state is None:

            return

        stage_id = AGENT_STAGE_MAP.get(agent_name, state.current_stage)

        self.set_stage(project_id, stage_id, status="active", detail=task)

        agent = state.agents.setdefault(
            agent_name,
            AgentRuntimeState(name=agent_name, stage=stage_id),
        )
        agent.status = "running"
        agent.current_task = task
        agent.started_at = datetime.utcnow().isoformat() + "Z"
        state.append_log(f"Agent started: {agent_name}")

    def mark_agent_finished(
        self,
        project_id: str,
        agent_name: str,
        *,
        success: bool,
        execution_time_ms: float = 0.0,
        token_usage: int = 0,
        tool_calls: int = 0,
    ) -> None:

        state = self._projects.get(project_id)

        if state is None:

            return

        agent = state.agents.setdefault(
            agent_name,
            AgentRuntimeState(name=agent_name),
        )
        agent.status = "completed" if success else "failed"
        agent.execution_time_ms = execution_time_ms
        agent.token_usage = token_usage
        agent.tool_calls = tool_calls
        agent.workload = min(100.0, agent.workload + (20.0 if success else 40.0))
        agent.finished_at = datetime.utcnow().isoformat() + "Z"
        agent.current_task = ""
        state.append_log(
            f"Agent finished: {agent_name} ({'success' if success else 'failed'})"
        )

    def finish_project(
        self,
        project_id: str,
        *,
        success: bool,
        metadata: dict | None = None,
    ) -> None:

        state = self._projects.get(project_id)

        if state is None:

            return

        state.status = "finished" if success else "failed"
        state.finished_at = datetime.utcnow().isoformat() + "Z"

        if success:

            for stage in state.workflow_stages:

                if stage.status == "active":

                    stage.status = "completed"
                    stage.finished_at = datetime.utcnow().isoformat() + "Z"

            self.set_stage(
                project_id,
                "completed",
                status="completed",
            )

        else:

            for stage in state.workflow_stages:

                if stage.status == "active":

                    stage.status = "failed"
                    stage.finished_at = datetime.utcnow().isoformat() + "Z"

                    if not stage.detail:

                        stage.detail = "Pipeline failed"

        if metadata:

            state.metadata.update(metadata)

        state.append_log(
            f"Project {'completed' if success else 'failed'}"
        )

    def update_git_log(
        self,
        project_id: str,
        entry: dict,
    ) -> None:

        state = self._projects.get(project_id)

        if state is None:

            return

        state.git_log.append(entry)
        self.set_stage(project_id, "git", status="active")

    def update_deployment(
        self,
        project_id: str,
        log: dict,
    ) -> None:

        state = self._projects.get(project_id)

        if state is None:

            return

        state.deployment_log = log
        status = "completed" if log.get("success") else "failed"
        self.set_stage(project_id, "deployment", status=status)

    def update_operations(
        self,
        project_id: str,
        log: dict,
    ) -> None:

        state = self._projects.get(project_id)

        if state is None:

            return

        state.operations_log = log
        status = "completed" if log.get("success", True) else "failed"
        self.set_stage(project_id, "operations", status=status)


_state_store: DashboardStateStore | None = None


def get_state_store() -> DashboardStateStore:

    global _state_store

    if _state_store is None:

        _state_store = DashboardStateStore()

    return _state_store
