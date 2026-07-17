from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from applications.platform.audit_manager import AuditManager
from applications.platform.configuration_manager import ConfigurationManager
from applications.platform.governance_manager import GovernanceManager
from applications.platform.model_manager import ModelManager
from applications.platform.organization_manager import OrganizationManager
from applications.platform.permission_manager import PermissionManager
from applications.platform.platform_result import PlatformContext
from applications.platform.platform_result import PlatformEventType
from applications.platform.platform_result import TeamType
from applications.platform.platform_store import PlatformStore
from applications.platform.project_registry import ProjectRegistry
from applications.platform.settings import PlatformSettings
from applications.platform.team_manager import TeamManager
from applications.platform.platform_memory import PlatformMemoryHelper
from applications.platform.workspace_manager import EnterpriseWorkspaceManager
from applications.software_team.coordinator.coordinator import CoordinatorResult
from applications.software_team.coordinator.coordinator import SoftwareTeamCoordinator
from applications.software_team.config.settings import SoftwareTeamSettings


@dataclass
class EnterpriseCoordinatorResult:
    """
    企业平台协调结果。
    """

    success: bool
    content: str
    platform_context: PlatformContext = field(default_factory=PlatformContext)
    team_result: CoordinatorResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class EnterpriseCoordinator:
    """
    企业级协调器：Organization → Workspace → Project → Team → SoftwareTeam。

    支持多 Team、多 Project、多 Workspace 统一调度。
    """

    def __init__(
        self,
        platform_settings: PlatformSettings | None = None,
        team_settings: SoftwareTeamSettings | None = None,
        governance: GovernanceManager | None = None,
        team_coordinator: SoftwareTeamCoordinator | None = None,
    ):

        self._platform_settings = platform_settings or PlatformSettings()
        self._store = PlatformStore(settings=self._platform_settings)
        self._governance = governance or GovernanceManager(
            settings=self._platform_settings,
            store=self._store,
        )

        team_config = team_settings or SoftwareTeamSettings()

        if self._governance.enabled:

            overrides = ConfigurationManager(
                settings=self._platform_settings,
            ).apply_to_software_team_settings()

            team_config = team_config.model_copy(update=overrides)

        self._team_coordinator = team_coordinator or SoftwareTeamCoordinator(
            settings=team_config,
        )

    @property
    def governance(self) -> GovernanceManager:

        return self._governance

    @property
    def organization(self) -> OrganizationManager:

        return self._governance._org

    @property
    def workspace(self) -> EnterpriseWorkspaceManager:

        return self._governance._workspace

    @property
    def projects(self) -> ProjectRegistry:

        return self._governance.projects

    @property
    def teams(self) -> TeamManager:

        return self._governance._teams

    @property
    def models(self) -> ModelManager:

        return self._governance._models

    @property
    def permissions(self) -> PermissionManager:

        return self._governance._permissions

    @property
    def audit(self) -> AuditManager:

        return self._governance.audit

    @property
    def configuration(self) -> ConfigurationManager:

        return self._governance._config

    @property
    def team_coordinator(self) -> SoftwareTeamCoordinator:

        return self._team_coordinator

    def run(
        self,
        *,
        session_id: str,
        user_requirement: str,
        project_name: str | None = None,
        user_id: str = "system",
        team_type: TeamType = TeamType.SOFTWARE,
        on_registered_project=None,
    ) -> EnterpriseCoordinatorResult:
        """
        企业级软件研发全流程。
        """

        name = project_name or user_requirement[:30]

        platform_prep = self._governance.prepare_project_run(
            project_name=name,
            requirement=user_requirement,
            user_id=user_id,
            team_type=team_type,
        )

        if not platform_prep.success:

            return EnterpriseCoordinatorResult(
                success=False,
                content=platform_prep.error_message or "Platform prep failed",
                platform_context=platform_prep.context,
                metadata=platform_prep.metadata,
            )

        self._save_platform_memory(
            session_id=session_id,
            context=platform_prep.context,
            content=f"Platform prep: {name}",
            event_type=PlatformEventType.PROJECT,
            user_id=user_id,
            init_metadata=platform_prep.metadata,
        )

        registered_id = platform_prep.metadata.get("registered_project_id", "")

        if on_registered_project is not None and registered_id:

            on_registered_project(registered_id)

        if team_type != TeamType.SOFTWARE:

            self._governance.finalize_project_run(
                project_id=registered_id,
                user_id=user_id,
                success=True,
            )

            return EnterpriseCoordinatorResult(
                success=True,
                content=(
                    f"Team {team_type.value} registered. "
                    f"Software execution only supported for software_team."
                ),
                platform_context=platform_prep.context,
                metadata={
                    **platform_prep.metadata,
                    "team_type": team_type.value,
                },
            )

        team_result = self._team_coordinator.run(
            session_id=session_id,
            user_requirement=user_requirement,
            project_name=project_name,
        )

        platform_context = platform_prep.context

        if team_result.project.workspace_path:

            self._governance.projects.update_workspace_path(
                registered_id,
                team_result.project.workspace_path,
            )

        finalize = self._governance.finalize_project_run(
            project_id=registered_id,
            user_id=user_id,
            success=team_result.success,
        )

        if finalize.context.organization_summary:

            platform_context = finalize.context

        self._save_platform_memory(
            session_id=session_id,
            context=platform_context,
            content=f"Project finalized: success={team_result.success}",
            event_type=PlatformEventType.AUDIT,
            user_id=user_id,
            init_metadata={"registered_project_id": registered_id},
        )

        self._tag_artifacts(platform_context, team_result)

        return EnterpriseCoordinatorResult(
            success=team_result.success,
            content=team_result.content,
            platform_context=platform_context,
            team_result=team_result,
            metadata={
                "registered_project_id": registered_id,
                "platform": platform_prep.metadata,
                "audit_count": len(platform_prep.audit_records),
            },
        )

    def _tag_artifacts(
        self,
        context: PlatformContext,
        team_result: CoordinatorResult,
    ) -> None:

        artifact_manager = self._team_coordinator.artifact_manager

        for artifact in team_result.artifacts:

            artifact.metadata.setdefault("platform_scope", "project")
            artifact.metadata["organization"] = context.organization_summary[:80]
            artifact.metadata["workspace"] = context.workspace_summary[:80]

            artifact_manager.register_platform_artifact(artifact)

    def _save_platform_memory(
        self,
        *,
        session_id: str,
        context: PlatformContext,
        content: str,
        event_type: PlatformEventType,
        user_id: str,
        init_metadata: dict,
    ) -> None:

        try:
            from applications.software_team.runtime.team_agent_runtime import (
                TeamAgentRuntime,
            )

            runtime = TeamAgentRuntime(settings=self._team_coordinator._settings)
        except Exception:

            return

        scope = self._governance.build_memory_scope(
            organization_id=init_metadata.get("organization_id", ""),
            workspace_id=init_metadata.get("workspace_id", ""),
            project_id=init_metadata.get("registered_project_id", ""),
            user_id=user_id,
        )

        scoped_session = PlatformMemoryHelper.scoped_session_id(
            session_id,
            scope,
        )

        PlatformMemoryHelper.save(
            runtime.memory_manager,
            scoped_session,
            content,
            event_type=event_type,
            scope=scope,
            metadata={"platform_context": context.to_shared_context()},
        )
