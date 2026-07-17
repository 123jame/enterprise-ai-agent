"""
P12 Enterprise Platform & Governance 测试。

运行:
    cd backend
    python -m applications.platform.tests.test_platform
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.memory.manager import MemoryManager

from applications.platform.audit_manager import AuditManager
from applications.platform.configuration_manager import ConfigurationManager
from applications.platform.enterprise_coordinator import EnterpriseCoordinator
from applications.platform.governance_manager import GovernanceManager
from applications.platform.model_manager import ModelManager
from applications.platform.organization_manager import OrganizationManager
from applications.platform.permission_manager import PermissionManager
from applications.platform.platform_memory import PlatformMemoryHelper
from applications.platform.platform_result import AuditCategory
from applications.platform.platform_result import Department
from applications.platform.platform_result import Member
from applications.platform.platform_result import ModelProvider
from applications.platform.platform_result import PermissionAction
from applications.platform.platform_result import PlatformContext
from applications.platform.platform_result import PlatformEventType
from applications.platform.platform_result import PolicyType
from applications.platform.platform_result import TeamType
from applications.platform.platform_store import PlatformStore
from applications.platform.project_registry import ProjectRegistry
from applications.platform.settings import PlatformSettings
from applications.platform.team_manager import TeamManager
from applications.platform.workspace_manager import EnterpriseWorkspaceManager
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.coordinator.coordinator import CoordinatorResult
from applications.software_team.coordinator.coordinator import SoftwareTeamCoordinator
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.artifact import Artifact
from applications.software_team.project.models.project import Project
from applications.software_team.project.models.project_status import ProjectStatus


def _platform_settings(root: Path) -> PlatformSettings:

    return PlatformSettings(
        enable_platform=True,
        platform_data_root=root / "platform_data",
        workspace_root=root / "workspace",
        enforce_permissions=False,
        enforce_governance=True,
    )


def test_organization_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        settings = _platform_settings(Path(tmp))
        store = PlatformStore(settings=settings)
        manager = OrganizationManager(settings=settings, store=store)

        org = manager.create_organization("Acme Corp")
        assert org.name == "Acme Corp"

        dept = Department.create("Engineering")
        updated = manager.add_department(org.id, dept)
        assert updated is not None
        assert len(updated.departments) == 1

        member = Member.create("alice", role="developer")
        updated = manager.add_member(org.id, member)
        assert updated is not None
        assert len(updated.members) == 1

        default = manager.get_or_create_default()
        assert default.id == org.id

        print("OrganizationManager: PASS")


def test_workspace_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        settings = _platform_settings(Path(tmp))
        store = PlatformStore(settings=settings)
        org = OrganizationManager(settings=settings, store=store).create_organization(
            "Org"
        )
        manager = EnterpriseWorkspaceManager(settings=settings, store=store)

        ws = manager.create(name="dev", organization_id=org.id)
        assert ws.organization_id == org.id

        default = manager.get_or_create_default(org.id)
        assert default.id == ws.id

        print("EnterpriseWorkspaceManager: PASS")


def test_project_registry() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        settings = _platform_settings(Path(tmp))
        store = PlatformStore(settings=settings)
        registry = ProjectRegistry(settings=settings, store=store)

        project = registry.register(
            name="Demo",
            organization_id="org-1",
            workspace_id="ws-1",
            team_type=TeamType.SOFTWARE,
            requirement="Build demo",
            owner_id="alice",
        )

        assert project.status == "created"
        assert registry.get(project.id) is not None

        updated = registry.update_status(project.id, "running")
        assert updated is not None
        assert updated.status == "running"

        path_updated = registry.update_workspace_path(
            project.id,
            "/tmp/demo",
        )
        assert path_updated is not None
        assert path_updated.workspace_path == "/tmp/demo"

        print("ProjectRegistry: PASS")


def test_team_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        settings = _platform_settings(Path(tmp))
        store = PlatformStore(settings=settings)
        manager = TeamManager(settings=settings, store=store)

        software = manager.get_or_create_default("org-1", TeamType.SOFTWARE)
        qa = manager.get_or_create_default("org-1", TeamType.QA)

        assert software.team_type == TeamType.SOFTWARE
        assert qa.team_type == TeamType.QA
        assert software.id != qa.id

        print("TeamManager: PASS")


def test_model_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        settings = _platform_settings(Path(tmp))
        store = PlatformStore(settings=settings)
        manager = ModelManager(settings=settings, store=store)

        models = manager.initialize_defaults()
        assert len(models) >= 3

        routed = manager.route(provider=ModelProvider.OPENAI)
        assert routed is not None
        assert routed.provider == ModelProvider.OPENAI

        print("ModelManager: PASS")


def test_permission_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        settings = _platform_settings(Path(tmp))
        store = PlatformStore(settings=settings)
        manager = PermissionManager(settings=settings, store=store)

        roles = manager.initialize_defaults()
        assert any(role.name == "admin" for role in roles)

        manager.grant(
            subject_type="user",
            subject_id="bob",
            resource_type="project",
            resource_id="*",
            action=PermissionAction.READ,
        )

        assert manager.check(
            subject_type="user",
            subject_id="bob",
            resource_type="project",
            resource_id="p1",
            action=PermissionAction.READ,
        )

        summary = manager.summarize_permissions(subject_id="bob")
        assert "bob" in summary or "project" in summary

        print("PermissionManager: PASS")


def test_audit_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        settings = _platform_settings(Path(tmp))
        store = PlatformStore(settings=settings)
        manager = AuditManager(settings=settings, store=store)

        prompt_audit = manager.record_prompt(
            actor="alice",
            agent_name="ProductAgent",
            detail="system prompt built",
        )
        tool_audit = manager.record(
            category=AuditCategory.TOOL_CALL,
            actor="ProductAgent",
            action="read_file",
            resource="p1",
            detail="read_file docs/PRD.md",
        )

        records = manager.list_records()
        assert len(records) >= 2
        assert prompt_audit.id in {record.id for record in records}
        assert tool_audit.id in {record.id for record in records}

        project_records = manager.list_records(resource="p1")
        assert len(project_records) == 1

        print("AuditManager: PASS")


def test_configuration_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        settings = _platform_settings(Path(tmp))
        manager = ConfigurationManager(settings=settings)

        config = manager.load()
        assert "llm" in config

        overrides = manager.apply_to_software_team_settings()
        assert isinstance(overrides, dict)

        print("ConfigurationManager: PASS")


def test_governance_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        settings = _platform_settings(Path(tmp))
        governance = GovernanceManager(settings=settings)

        init = governance.initialize_platform(actor="tester")
        assert init.success is True
        assert init.metadata.get("organization_id")

        prep = governance.prepare_project_run(
            project_name="Governed Project",
            requirement="Build API",
            user_id="tester",
        )
        assert prep.success is True
        assert prep.context.organization_summary
        assert prep.metadata.get("registered_project_id")

        project_id = prep.metadata["registered_project_id"]
        final = governance.finalize_project_run(
            project_id=project_id,
            user_id="tester",
            success=True,
        )
        assert final.success is True
        assert final.metadata.get("status") == "finished"

        assert governance.check_policy(
            PolicyType.AGENT,
            {"team_type": "software"},
        )

        print("GovernanceManager: PASS")


def test_platform_memory_helper() -> None:

    memory = MemoryManager()
    scope = GovernanceManager().build_memory_scope(
        organization_id="org-1",
        workspace_id="ws-1",
        project_id="proj-1",
        user_id="alice",
    )

    scoped = PlatformMemoryHelper.scoped_session_id("sess-1", scope)
    assert "org:org-1" in scoped
    assert "proj:proj-1" in scoped

    PlatformMemoryHelper.save(
        memory,
        scoped,
        "Platform initialized",
        event_type=PlatformEventType.ORGANIZATION,
        scope=scope,
    )

    history = memory.load(scoped)
    assert len(history.records) >= 1

    print("PlatformMemoryHelper: PASS")


def test_team_prompt_builder_platform_context() -> None:

    from applications.software_team.agents.base.coordinator_context import (
        CoordinatorContext,
    )
    from applications.software_team.prompt.team_prompt_builder import TeamPromptBuilder

    project = Project(
        id="p1",
        name="Demo",
        requirement="Build demo",
        workspace_path="/tmp/demo",
        status=ProjectStatus.PLANNING,
        tech_stack=["python"],
    )

    context = CoordinatorContext(
        session_id="sess-1",
        user_message="Build demo",
        project=project,
        metadata={},
        shared_context={},
    )

    platform_ctx = PlatformContext(
        organization_summary="Acme Corp",
        workspace_summary="dev workspace",
        permission_summary="admin access",
        project_summary="Demo project",
    )

    messages = TeamPromptBuilder().build(
        "ProductAgent",
        context,
        ArtifactManager(),
        platform_context=platform_ctx,
    )

    combined = "\n".join(message.content for message in messages)
    assert "Enterprise Platform Context" in combined
    assert "Acme Corp" in combined

    print("TeamPromptBuilder PlatformContext: PASS")


def test_artifact_manager_platform_scope() -> None:

    manager = ArtifactManager()
    artifact = Artifact(
        id="art-1",
        name="org-policy",
        type="policy",
        path="/policies/default",
        owner="GovernanceManager",
        metadata={"platform_scope": "organization"},
    )

    manager.register_platform_artifact(artifact)
    found = manager.find_by_scope("organization")

    assert len(found) == 1
    assert found[0].metadata.get("stage") == "platform"

    print("ArtifactManager platform scope: PASS")


class _MockTeamCoordinator:
    """
    轻量 Mock，避免完整 Software Team Pipeline。
    """

    def __init__(self, workspace_path: str):

        self._settings = SoftwareTeamSettings()
        self._artifact_manager = ArtifactManager()
        self._workspace_path = workspace_path

    @property
    def artifact_manager(self) -> ArtifactManager:

        return self._artifact_manager

    def run(
        self,
        *,
        session_id: str,
        user_requirement: str,
        project_name: str | None = None,
    ) -> CoordinatorResult:

        project = Project(
            id="local-proj",
            name=project_name or "Mock",
            requirement=user_requirement,
            workspace_path=self._workspace_path,
            status=ProjectStatus.FINISHED,
            tech_stack=["python"],
        )

        artifact = Artifact(
            id="art-mock-1",
            name="mock-output",
            type="code",
            path=f"{self._workspace_path}/main.py",
            owner="DeveloperAgent",
        )

        self._artifact_manager.add(artifact)

        return CoordinatorResult(
            success=True,
            project=project,
            content="Mock workflow completed",
            artifacts=[artifact],
        )


def test_enterprise_coordinator() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        settings = _platform_settings(root)
        workspace_path = str(root / "proj-workspace")
        Path(workspace_path).mkdir(parents=True, exist_ok=True)

        mock_team = _MockTeamCoordinator(workspace_path=workspace_path)

        coordinator = EnterpriseCoordinator(
            platform_settings=settings,
            team_coordinator=mock_team,  # type: ignore[arg-type]
        )

        result = coordinator.run(
            session_id="ent-sess-1",
            user_requirement="Build inventory system",
            project_name="Inventory",
            user_id="tester",
        )

        assert result.success is True
        assert result.platform_context.organization_summary
        assert result.team_result is not None
        assert result.metadata.get("registered_project_id")

        project_id = result.metadata["registered_project_id"]
        registered = coordinator.projects.get(project_id)
        assert registered is not None
        assert registered.workspace_path == workspace_path

        platform_artifacts = mock_team.artifact_manager.find_by_scope("project")
        assert len(platform_artifacts) >= 1

        print("EnterpriseCoordinator: PASS")


def test_non_software_team_registration() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        settings = _platform_settings(Path(tmp))
        coordinator = EnterpriseCoordinator(platform_settings=settings)

        result = coordinator.run(
            session_id="qa-sess",
            user_requirement="QA review",
            project_name="QA Project",
            user_id="tester",
            team_type=TeamType.QA,
        )

        assert result.success is True
        assert "QA Team" in result.content or "qa" in result.content.lower()

        print("EnterpriseCoordinator non-software team: PASS")


def main() -> None:

    test_organization_manager()
    test_workspace_manager()
    test_project_registry()
    test_team_manager()
    test_model_manager()
    test_permission_manager()
    test_audit_manager()
    test_configuration_manager()
    test_governance_manager()
    test_platform_memory_helper()
    test_team_prompt_builder_platform_context()
    test_artifact_manager_platform_scope()
    test_enterprise_coordinator()
    test_non_software_team_registration()

    print("\n=== P12 Enterprise Platform & Governance: ALL PASS ===")


if __name__ == "__main__":

    main()
