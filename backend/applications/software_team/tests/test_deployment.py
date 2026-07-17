"""
P8 DevOps & Deployment 测试。

运行:
    cd backend
    python -m applications.software_team.tests.test_deployment
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from app.memory.manager import MemoryManager

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.deployment.build_manager import BuildManager
from applications.software_team.deployment.deploy_manager import DeployManager
from applications.software_team.deployment.deployment_result import DeployMode
from applications.software_team.deployment.deployment_result import DeploymentContext
from applications.software_team.deployment.deployment_service import DeploymentService
from applications.software_team.deployment.health_checker import HealthChecker
from applications.software_team.deployment.package_manager import PackageManager
from applications.software_team.deployment.release_manager import ReleaseManager
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.project import Project
from applications.software_team.project.models.project_status import ProjectStatus


def _create_sample_workspace(root: Path) -> None:

    root.mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text("# Sample\n", encoding="utf-8")

    backend = root / "backend"
    backend.mkdir(parents=True, exist_ok=True)
    (backend / "main.py").write_text(
        "app = object()\n",
        encoding="utf-8",
    )
    (backend / "requirements.txt").write_text(
        "# no external deps\n",
        encoding="utf-8",
    )


def test_build_manager_python() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _create_sample_workspace(root)

        settings = SoftwareTeamSettings(
            deployment_install_dependencies=False,
        )
        manager = BuildManager(settings=settings)
        result = manager.build(root)

        assert result.success is True
        assert result.workspace_path
        print("BuildManager: PASS")


def test_package_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _create_sample_workspace(root)

        manager = PackageManager()
        result = manager.package(root, project_name="Demo App")

        assert result.success is True
        assert Path(result.package_path).is_file()
        assert (root / "Dockerfile").is_file()
        assert (root / "docker-compose.yml").is_file()
        assert (root / "deploy" / "deploy.sh").is_file()
        print("PackageManager: PASS")


def test_deploy_manager_local() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _create_sample_workspace(root)

        PackageManager().package(root, project_name="Demo App")

        settings = SoftwareTeamSettings(deployment_mode="local")
        result = DeployManager(settings=settings).deploy(
            root,
            project_name="Demo App",
        )

        assert result.success is True
        assert result.mode == DeployMode.LOCAL
        assert result.deploy_url
        print("DeployManager (local): PASS")


def test_health_checker() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _create_sample_workspace(root)

        PackageManager().package(root, project_name="Demo App")

        settings = SoftwareTeamSettings(deployment_health_http=False)
        result = HealthChecker(settings=settings).check(root)

        assert result.success is True
        assert len(result.checks) >= 2
        print("HealthChecker: PASS")


def test_release_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _create_sample_workspace(root)

        project = Project(
            id="p1",
            name="Demo App",
            requirement="demo",
            workspace_path=str(root),
            status=ProjectStatus.DELIVERING,
        )

        settings = SoftwareTeamSettings(
            enable_git=False,
            deployment_version="1.0.0-test",
        )
        result = ReleaseManager(settings=settings).release(
            root,
            project=project,
            artifact_summary="- backend",
        )

        assert result.success is True
        assert result.version == "1.0.0-test"
        assert Path(result.release_notes_path).is_file()
        print("ReleaseManager: PASS")


def test_deployment_service_pipeline() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _create_sample_workspace(root)

        project = Project(
            id="p1",
            name="Demo App",
            requirement="demo deployment",
            workspace_path=str(root),
            status=ProjectStatus.DELIVERING,
        )

        artifact_manager = ArtifactManager()
        memory = MemoryManager()
        session_id = "test-deployment-session"

        settings = SoftwareTeamSettings(
            enable_deployment=True,
            enable_git=False,
            deployment_mode="local",
            deployment_install_dependencies=False,
            deployment_health_http=False,
            deployment_version="0.1.0-p8",
        )

        service = DeploymentService(settings=settings)
        result = service.run_pipeline(
            project,
            artifact_manager=artifact_manager,
            memory_manager=memory,
            session_id=session_id,
        )

        assert result.success is True
        assert result.build is not None and result.build.success
        assert result.package is not None and result.package.success
        assert result.deploy is not None and result.deploy.success
        assert result.health is not None and result.health.success
        assert result.release is not None and result.release.success

        deployment_artifacts = artifact_manager.find_deployment_artifacts()
        assert len(deployment_artifacts) >= 4

        memory_context = memory.load(session_id)
        categories = {
            r.metadata.get("category")
            for r in memory_context.records
            if r.metadata.get("type") == "memory"
        }

        assert "build_history" in categories
        assert "deployment_history" in categories
        assert "release_history" in categories
        print("DeploymentService pipeline: PASS")


def test_team_prompt_builder_deployment_context() -> None:

    from applications.software_team.agents.base.coordinator_context import (
        CoordinatorContext,
    )
    from applications.software_team.prompt.team_prompt_builder import (
        TeamPromptBuilder,
    )
    from app.agents.types import AgentContext

    project = Project(
        id="p1",
        name="Demo",
        requirement="demo",
        workspace_path="/tmp/ws",
        status=ProjectStatus.DELIVERING,
    )

    context = CoordinatorContext.from_agent_context(
        context=AgentContext(
            session_id="s1",
            user_message="fix deploy",
            metadata={},
        ),
        project=project,
    )

    deploy_ctx = DeploymentContext(
        build_summary="success=True targets=1",
        health_summary="Health: FAIL\n- [FAIL] http_health: unreachable",
        deploy_url="http://localhost:8000/api/health",
        version="0.1.0",
    )

    builder = TeamPromptBuilder()
    messages = builder.build(
        "ProductAgent",
        context,
        ArtifactManager(),
        deployment_context=deploy_ctx,
    )

    combined = "\n".join(m.content for m in messages)
    assert "Deployment Context" in combined
    assert "http_health" in combined
    print("TeamPromptBuilder deployment: PASS")


def test_deploy_manager_docker_skip() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _create_sample_workspace(root)
        PackageManager().package(root, project_name="Demo")

        settings = SoftwareTeamSettings(
            deployment_mode="docker",
            deployment_run_docker=False,
        )
        result = DeployManager(settings=settings).deploy(
            root,
            project_name="Demo",
        )

        if shutil.which("docker") is None:

            assert result.success is False
            print("DeployManager (docker, no docker): SKIP expected fail")
            return

        assert result.success is True
        assert result.mode == DeployMode.DOCKER
        print("DeployManager (docker skip): PASS")


def main() -> None:

    test_build_manager_python()
    test_package_manager()
    test_deploy_manager_local()
    test_health_checker()
    test_release_manager()
    test_deployment_service_pipeline()
    test_team_prompt_builder_deployment_context()
    test_deploy_manager_docker_skip()
    print("\nAll P8 deployment tests passed.")


if __name__ == "__main__":

    main()
