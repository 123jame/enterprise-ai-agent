from __future__ import annotations

from pathlib import Path

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.management.management_result import (
    ProjectManagementState,
)
from applications.software_team.project.models.project import Project
from applications.software_team.project.models.project_status import ProjectStatus
from applications.software_team.project.services.project_service import (
    ProjectService,
)


class ProjectManager:
    """
    管理整个项目生命周期。

    协调 ProjectService 与项目管理运行时状态，不直接调用 Agent。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        project_service: ProjectService | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._project_service = project_service
        self._states: dict[str, ProjectManagementState] = {}

    def initialize(
        self,
        project: Project,
    ) -> ProjectManagementState:

        state = ProjectManagementState(
            project_id=project.id,
            current_sprint=self._build_sprint_name(project),
        )

        self._states[project.id] = state

        if self._project_service is not None:

            self._project_service.update_status(ProjectStatus.PLANNING)

        return state

    def get_state(
        self,
        project_id: str,
    ) -> ProjectManagementState | None:

        return self._states.get(project_id)

    def ensure_state(
        self,
        project: Project,
    ) -> ProjectManagementState:

        state = self._states.get(project.id)

        if state is None:

            state = self.initialize(project)

        return state

    def mark_agent_completed(
        self,
        project: Project,
        agent_name: str,
    ) -> None:

        state = self.ensure_state(project)

        if agent_name not in state.completed_agents:

            state.completed_agents.append(agent_name)

    def mark_complete(
        self,
        project: Project,
        *,
        success: bool,
    ) -> None:

        if self._project_service is not None:

            self._project_service.update_status(
                ProjectStatus.FINISHED if success else ProjectStatus.FAILED,
            )

    def get_lifecycle_summary(
        self,
        project: Project,
    ) -> str:

        state = self._states.get(project.id)

        if state is None:

            return f"Project {project.name}: not initialized"

        return (
            f"Project: {project.name} ({project.status.value})\n"
            f"Sprint: {state.current_sprint}\n"
            f"Tasks: {len(state.tasks)}\n"
            f"Milestones: {len(state.milestones)}\n"
            f"Risks: {len(state.risks)}\n"
            f"Completed agents: {len(state.completed_agents)}"
        )

    def bind_state(
        self,
        project_id: str,
        state: ProjectManagementState,
    ) -> None:

        self._states[project_id] = state

    @staticmethod
    def _build_sprint_name(project: Project) -> str:

        slug = project.name.lower().replace(" ", "-")[:20]

        return f"Sprint-1-{slug}"
