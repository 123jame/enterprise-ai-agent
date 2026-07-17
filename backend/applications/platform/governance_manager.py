from __future__ import annotations

from applications.platform.audit_manager import AuditManager
from applications.platform.configuration_manager import ConfigurationManager
from applications.platform.model_manager import ModelManager
from applications.platform.organization_manager import OrganizationManager
from applications.platform.permission_manager import PermissionManager
from applications.platform.platform_result import AuditCategory
from applications.platform.platform_result import AuditRecord
from applications.platform.platform_result import MemoryScopeContext
from applications.platform.platform_result import PermissionAction
from applications.platform.platform_result import PlatformContext
from applications.platform.platform_result import PlatformEventType
from applications.platform.platform_result import PlatformPolicy
from applications.platform.platform_result import PlatformResult
from applications.platform.platform_result import PolicyType
from applications.platform.platform_result import RegisteredProject
from applications.platform.platform_result import TeamType
from applications.platform.platform_store import PlatformStore
from applications.platform.project_registry import ProjectRegistry
from applications.platform.settings import PlatformSettings
from applications.platform.team_manager import TeamManager
from applications.platform.workspace_manager import EnterpriseWorkspaceManager


class GovernanceManager:
    """
    统一治理：Agent / Prompt / Tool / Model Policy，编排平台全流程。
    """

    POLICIES_KEY = "policies"

    _DEFAULT_POLICIES: list[tuple[PolicyType, str, dict]] = [
        (
            PolicyType.AGENT,
            "agent_safety",
            {"max_iterations": 10, "require_verification": True},
        ),
        (
            PolicyType.PROMPT,
            "prompt_safety",
            {"max_prompt_length": 32000, "block_secrets": True},
        ),
        (
            PolicyType.TOOL,
            "tool_safety",
            {"allowed_tools": ["read_file", "write_file", "list_files", "search"]},
        ),
        (
            PolicyType.MODEL,
            "model_routing",
            {"prefer_provider": "openai", "fallback": "local"},
        ),
    ]

    def __init__(
        self,
        settings: PlatformSettings | None = None,
        store: PlatformStore | None = None,
        organization_manager: OrganizationManager | None = None,
        workspace_manager: EnterpriseWorkspaceManager | None = None,
        project_registry: ProjectRegistry | None = None,
        team_manager: TeamManager | None = None,
        model_manager: ModelManager | None = None,
        permission_manager: PermissionManager | None = None,
        audit_manager: AuditManager | None = None,
        configuration_manager: ConfigurationManager | None = None,
    ):

        self._settings = settings or PlatformSettings()
        self._store = store or PlatformStore(settings=self._settings)
        self._org = organization_manager or OrganizationManager(
            settings=self._settings,
            store=self._store,
        )
        self._workspace = workspace_manager or EnterpriseWorkspaceManager(
            settings=self._settings,
            store=self._store,
        )
        self._projects = project_registry or ProjectRegistry(
            settings=self._settings,
            store=self._store,
        )
        self._teams = team_manager or TeamManager(
            settings=self._settings,
            store=self._store,
        )
        self._models = model_manager or ModelManager(
            settings=self._settings,
            store=self._store,
        )
        self._permissions = permission_manager or PermissionManager(
            settings=self._settings,
            store=self._store,
        )
        self._audit = audit_manager or AuditManager(
            settings=self._settings,
            store=self._store,
        )
        self._config = configuration_manager or ConfigurationManager(
            settings=self._settings,
        )

    @property
    def enabled(self) -> bool:

        return self._settings.enable_platform

    @property
    def audit(self) -> AuditManager:

        return self._audit

    @property
    def projects(self) -> ProjectRegistry:

        return self._projects

    def initialize_platform(
        self,
        *,
        actor: str = "system",
    ) -> PlatformResult:

        if not self.enabled:

            return PlatformResult(success=True, metadata={"skipped": True})

        org = self._org.get_or_create_default()
        workspace = self._workspace.get_or_create_default(org.id)
        team = self._teams.get_or_create_default(org.id, TeamType.SOFTWARE)
        models = self._models.initialize_defaults()
        roles = self._permissions.initialize_defaults()
        policies = self.initialize_policies()
        config = self._config.load()

        audit = self._audit.record_platform(
            actor=actor,
            action="initialize_platform",
            resource=org.id,
            detail=f"workspace={workspace.id}, team={team.id}",
        )

        context = self.build_context(
            organization_id=org.id,
            workspace_id=workspace.id,
            user_id=actor,
        )

        return PlatformResult(
            success=True,
            context=context,
            audit_records=[audit],
            metadata={
                "organization_id": org.id,
                "workspace_id": workspace.id,
                "team_id": team.id,
                "models": len(models),
                "roles": len(roles),
                "policies": len(policies),
                "config_sections": len(config),
            },
        )

    def prepare_project_run(
        self,
        *,
        project_name: str,
        requirement: str,
        user_id: str = "system",
        team_type: TeamType = TeamType.SOFTWARE,
    ) -> PlatformResult:

        if not self.enabled:

            return PlatformResult(success=True, metadata={"skipped": True})

        init = self.initialize_platform(actor=user_id)
        org_id = init.metadata.get("organization_id", "")
        workspace_id = init.metadata.get("workspace_id", "")

        if not self._permissions.check(
            subject_type="user",
            subject_id=user_id,
            resource_type="project",
            resource_id="*",
            action=PermissionAction.WRITE,
        ):

            return PlatformResult(
                success=False,
                error_message=f"Permission denied for user {user_id}",
            )

        team = self._teams.get_or_create_default(org_id, team_type)

        if not self.check_policy(PolicyType.AGENT, {"team_type": team_type.value}):

            return PlatformResult(
                success=False,
                error_message="Agent policy check failed",
            )

        registered = self._projects.register(
            name=project_name,
            organization_id=org_id,
            workspace_id=workspace_id,
            team_type=team_type,
            requirement=requirement,
            owner_id=user_id,
        )

        self._workspace.register_project(workspace_id, registered.id)

        audit = self._audit.record_workflow(
            actor=user_id,
            project_id=registered.id,
            action="register_project",
            detail=f"team={team.team_type.value}",
        )

        context = self.build_context(
            organization_id=org_id,
            workspace_id=workspace_id,
            project_id=registered.id,
            user_id=user_id,
            team=team,
        )

        return PlatformResult(
            success=True,
            context=context,
            audit_records=[audit],
            metadata={
                "organization_id": org_id,
                "workspace_id": workspace_id,
                "registered_project_id": registered.id,
                "team_id": team.id,
                "team_type": team.team_type.value,
            },
        )

    def finalize_project_run(
        self,
        *,
        project_id: str,
        user_id: str = "system",
        success: bool = True,
    ) -> PlatformResult:

        project = self._projects.get(project_id)

        if project is None:

            return PlatformResult(
                success=False,
                error_message=f"Project not found: {project_id}",
            )

        status = "finished" if success else "failed"
        self._projects.update_status(project_id, status)

        audit = self._audit.record_workflow(
            actor=user_id,
            project_id=project_id,
            action="finalize_project",
            detail=f"status={status}",
        )

        context = self.build_context(
            organization_id=project.organization_id,
            workspace_id=project.workspace_id,
            project_id=project_id,
            user_id=user_id,
        )

        return PlatformResult(
            success=True,
            context=context,
            audit_records=[audit],
            metadata={"status": status},
        )

    def initialize_policies(self) -> list[PlatformPolicy]:

        if self._store.load(self.POLICIES_KEY):

            return self.list_policies()

        policies: list[PlatformPolicy] = []

        for policy_type, name, rules in self._DEFAULT_POLICIES:

            policy = PlatformPolicy.create(
                policy_type=policy_type,
                name=name,
                rules=rules,
            )
            self._store.append(self.POLICIES_KEY, self._policy_to_dict(policy))
            policies.append(policy)

        return policies

    def list_policies(self) -> list[PlatformPolicy]:

        return [
            self._dict_to_policy(item)
            for item in self._store.load(self.POLICIES_KEY)
        ]

    def check_policy(
        self,
        policy_type: PolicyType,
        context: dict,
    ) -> bool:

        if not self._settings.enforce_governance:

            return True

        for policy in self.list_policies():

            if policy.policy_type != policy_type or not policy.enabled:

                continue

            if policy_type == PolicyType.TOOL:

                allowed = policy.rules.get("allowed_tools", [])

                tool = context.get("tool_name")

                if tool and allowed and tool not in allowed:

                    return False

        return True

    def build_context(
        self,
        *,
        organization_id: str = "",
        workspace_id: str = "",
        project_id: str = "",
        user_id: str = "",
        team=None,
    ) -> PlatformContext:

        org = self._org.get_organization(organization_id) if organization_id else None
        workspace = self._workspace.get(workspace_id) if workspace_id else None
        project = self._projects.get(project_id) if project_id else None
        models = self._models.list_models()

        if team is None and organization_id:

            team = self._teams.get_or_create_default(organization_id)

        return PlatformContext(
            organization_summary=(
                OrganizationManager.summarize(org) if org else "n/a"
            ),
            workspace_summary=(
                EnterpriseWorkspaceManager.summarize(workspace)
                if workspace
                else "n/a"
            ),
            permission_summary=self._permissions.summarize_permissions(
                subject_id=user_id or "system",
            ),
            project_summary=(
                ProjectRegistry.summarize(project) if project else "n/a"
            ),
            team_summary=(
                TeamManager.summarize(team) if team else "n/a"
            ),
            model_summary=ModelManager.summarize(models),
            governance_summary=self._governance_summary(),
        )

    def build_memory_scope(
        self,
        *,
        organization_id: str = "",
        workspace_id: str = "",
        project_id: str = "",
        user_id: str = "",
    ) -> MemoryScopeContext:

        return MemoryScopeContext(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
        )

    def _governance_summary(self) -> str:

        policies = self.list_policies()
        enabled = [p for p in policies if p.enabled]

        lines = [f"Policies: {len(enabled)}/{len(policies)} enabled"]

        for policy in enabled[:4]:

            lines.append(f"- [{policy.policy_type.value}] {policy.name}")

        return "\n".join(lines)

    @staticmethod
    def _policy_to_dict(policy: PlatformPolicy) -> dict:

        return {
            "id": policy.id,
            "policy_type": policy.policy_type.value,
            "name": policy.name,
            "rules": policy.rules,
            "enabled": policy.enabled,
        }

    @staticmethod
    def _dict_to_policy(data: dict) -> PlatformPolicy:

        return PlatformPolicy(
            id=data["id"],
            policy_type=PolicyType(data["policy_type"]),
            name=data["name"],
            rules=data.get("rules", {}),
            enabled=data.get("enabled", True),
        )
