from __future__ import annotations

import re
import threading
from typing import Any
from uuid import uuid4

from applications.dashboard.event_listener import DashboardEventListener
from applications.dashboard.event_types import AGENT_STAGE_MAP
from applications.dashboard.state_store import get_state_store
from applications.platform.enterprise_coordinator import EnterpriseCoordinator
from applications.platform.settings import PlatformSettings
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.coordinator.coordinator import SoftwareTeamCoordinator
from applications.software_team.project.models.project_status import ProjectStatus
from applications.software_team.workflow.pipeline import SoftwareTeamPipeline


class DashboardRunService:
    """
    在后台线程启动 EnterpriseCoordinator，并通过事件监听器推送状态。
    """

    def __init__(
        self,
        platform_settings: PlatformSettings | None = None,
        team_settings: SoftwareTeamSettings | None = None,
    ):

        self._platform_settings = platform_settings or PlatformSettings()
        self._team_settings = team_settings or SoftwareTeamSettings()

    def start_project(
        self,
        *,
        requirement: str,
        project_name: str | None = None,
        user_id: str = "dashboard",
    ) -> dict[str, Any]:

        session_id = f"sess_{uuid4().hex[:12]}"
        name = project_name or requirement[:40]
        placeholder_id = f"pending_{uuid4().hex[:8]}"

        listener = DashboardEventListener(
            project_id=placeholder_id,
            session_id=session_id,
        )
        listener.on_project_started(name, requirement)
        listener.on_workflow_status("requirement", "completed")
        listener.on_workflow_status("planning", "active")

        thread = threading.Thread(
            target=self._run_project,
            kwargs={
                "session_id": session_id,
                "requirement": requirement,
                "project_name": name,
                "user_id": user_id,
                "listener": listener,
                "placeholder_id": placeholder_id,
            },
            daemon=True,
        )
        thread.start()

        return {
            "session_id": session_id,
            "project_id": placeholder_id,
            "name": name,
            "requirement": requirement,
            "status": "running",
        }

    def _run_project(
        self,
        *,
        session_id: str,
        requirement: str,
        project_name: str,
        user_id: str,
        listener: DashboardEventListener,
        placeholder_id: str,
    ) -> None:

        def bind_registered_project(registered_id: str) -> None:

            if registered_id and registered_id != placeholder_id:

                get_state_store().migrate_project_id(
                    placeholder_id,
                    registered_id,
                )
                listener._project_id = registered_id

        try:

            coordinator = self._build_coordinator(listener)
            result = coordinator.run(
                session_id=session_id,
                user_requirement=requirement,
                project_name=project_name,
                user_id=user_id,
                on_registered_project=bind_registered_project,
            )

            registered_id = result.metadata.get(
                "registered_project_id",
                listener._project_id,
            )

            bind_registered_project(registered_id)

            failed_agent = _extract_failed_agent(result)

            if result.success:

                listener.on_workflow_status("knowledge", "completed")

            else:

                stage = _resolve_failure_stage(failed_agent, result.content)
                listener.on_workflow_status(
                    stage,
                    "failed",
                    detail=result.content[:300],
                )

            listener.on_project_finished(
                success=result.success,
                metadata={
                    "registered_project_id": registered_id,
                    "content": result.content[:500],
                    "failed_agent": failed_agent,
                },
            )

        except Exception as error:

            listener.on_log(str(error))
            listener.on_project_finished(
                success=False,
                metadata={"error": str(error)},
            )

    def _build_coordinator(
        self,
        listener: DashboardEventListener,
    ) -> EnterpriseCoordinator:

        team_coordinator = SoftwareTeamCoordinator(
            settings=self._team_settings,
        )

        existing = team_coordinator._workflow_runner

        if isinstance(existing, SoftwareTeamPipeline):

            pipeline = existing
        else:

            pipeline = SoftwareTeamPipeline(
                project_service=team_coordinator._project_service,
                artifact_manager=team_coordinator._artifact_manager,
                workspace_manager=team_coordinator._workspace_manager,
                settings=team_coordinator._settings,
            )

        pipeline._on_status_change = _status_callback(listener)
        pipeline._on_agent_started = listener.on_agent_started
        pipeline._on_agent_finished = listener.on_agent_finished
        pipeline._on_git_event = listener.on_git_update
        pipeline._on_deployment_finished = listener.on_deployment_finished
        pipeline._on_operation_update = listener.on_operation_update

        team_coordinator._workflow_runner = pipeline

        return EnterpriseCoordinator(
            platform_settings=self._platform_settings,
            team_settings=self._team_settings,
            team_coordinator=team_coordinator,
        )


def _status_callback(listener: DashboardEventListener):

    stage_map = {
        ProjectStatus.PLANNING.value: "planning",
        ProjectStatus.DESIGNING.value: "architecture",
        ProjectStatus.DEVELOPING.value: "development",
        ProjectStatus.TESTING.value: "verification",
        ProjectStatus.REVIEWING.value: "verification",
        ProjectStatus.DELIVERING.value: "deployment",
        ProjectStatus.FINISHED.value: "completed",
    }

    def callback(status: ProjectStatus) -> None:

        if status == ProjectStatus.FINISHED:

            listener.on_workflow_status(
                "completed",
                "completed",
                detail=status.value,
            )
            return

        if status == ProjectStatus.FAILED:

            state = get_state_store().get(listener._project_id)
            failed_stage = state.current_stage if state else "development"

            listener.on_workflow_status(
                failed_stage,
                "failed",
                detail=status.value,
            )
            return

        stage = stage_map.get(status.value, status.value)
        listener.on_workflow_status(stage, "active", detail=status.value)

    return callback


_SERVICE_FAILURE_STAGE = {
    "DeploymentService": "deployment",
    "GitService": "git",
    "OperationsService": "operations",
}


def _extract_failed_agent(result) -> str:

    team = result.team_result

    if team is not None:

        agent = team.metadata.get("failed_agent", "")

        if agent:

            return str(agent)

    match = re.search(r"Pipeline 在 (\S+) 失败", result.content or "")

    if match:

        return match.group(1)

    return ""


def _resolve_failure_stage(failed_agent: str, content: str) -> str:

    if failed_agent in _SERVICE_FAILURE_STAGE:

        return _SERVICE_FAILURE_STAGE[failed_agent]

    if failed_agent in AGENT_STAGE_MAP:

        return AGENT_STAGE_MAP[failed_agent]

    lowered = (content or "").lower()

    if "deployment" in lowered:

        return "deployment"

    if "git" in lowered:

        return "git"

    return "planning"


_run_service: DashboardRunService | None = None


def get_run_service() -> DashboardRunService:

    global _run_service

    if _run_service is None:

        _run_service = DashboardRunService()

    return _run_service
