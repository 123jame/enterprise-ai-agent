from __future__ import annotations

from uuid import uuid4

from pathlib import Path

from app.memory.manager import MemoryManager

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.deployment.build_manager import BuildManager
from applications.software_team.deployment.deploy_manager import DeployManager
from applications.software_team.deployment.deployment_result import (
    DeploymentContext,
)
from applications.software_team.deployment.deployment_result import (
    DeploymentEventType,
)
from applications.software_team.deployment.deployment_result import (
    DeploymentPipelineResult,
)
from applications.software_team.deployment.health_checker import HealthChecker
from applications.software_team.deployment.package_manager import PackageManager
from applications.software_team.deployment.release_manager import ReleaseManager
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.artifact import Artifact
from applications.software_team.project.models.project import Project


class DeploymentService:
    """
    DevOps 部署流水线编排：Build → Package → Deploy → Health → Release。

    供 Pipeline / Coordinator 调用，Agent 不直接执行部署命令。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        build_manager: BuildManager | None = None,
        package_manager: PackageManager | None = None,
        deploy_manager: DeployManager | None = None,
        health_checker: HealthChecker | None = None,
        release_manager: ReleaseManager | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._build = build_manager or BuildManager(settings=self._settings)
        self._package = package_manager or PackageManager(
            settings=self._settings,
        )
        self._deploy = deploy_manager or DeployManager(
            settings=self._settings,
        )
        self._health = health_checker or HealthChecker(
            settings=self._settings,
        )
        self._release = release_manager or ReleaseManager(
            settings=self._settings,
        )

    @property
    def enabled(self) -> bool:

        return self._settings.enable_deployment

    def run_pipeline(
        self,
        project: Project,
        *,
        artifact_manager: ArtifactManager,
        memory_manager: MemoryManager | None = None,
        session_id: str = "",
    ) -> DeploymentPipelineResult:
        """
        执行完整 DevOps 流水线。
        """

        if not self.enabled:

            return DeploymentPipelineResult(
                success=True,
                metadata={"skipped": True},
            )

        workspace = project.workspace_path

        build_result = self._build.build(workspace)

        self._save_memory(
            memory_manager,
            session_id,
            DeploymentEventType.BUILD,
            f"Build {'ok' if build_result.success else 'failed'}: "
            f"{build_result.error_message or build_result.target}",
            {"target": build_result.target},
        )

        if not build_result.success:

            return DeploymentPipelineResult(
                success=False,
                build=build_result,
                error_message=build_result.error_message,
            )

        package_result = self._package.package(
            workspace,
            project_name=project.name,
        )

        self._register_package_artifacts(
            artifact_manager,
            project,
            package_result,
        )

        self._save_memory(
            memory_manager,
            session_id,
            DeploymentEventType.PACKAGE,
            f"Package created: {package_result.package_path}",
            {"package_type": package_result.package_type},
        )

        deploy_result = self._deploy.deploy(
            workspace,
            project_name=project.name,
        )

        self._save_memory(
            memory_manager,
            session_id,
            DeploymentEventType.DEPLOY,
            deploy_result.message or deploy_result.error_message,
            {"mode": deploy_result.mode.value},
        )

        if not deploy_result.success:

            return DeploymentPipelineResult(
                success=False,
                build=build_result,
                package=package_result,
                deploy=deploy_result,
                error_message=deploy_result.error_message,
            )

        health_result = self._health.check(
            workspace,
            deploy_url=deploy_result.deploy_url,
        )

        self._save_memory(
            memory_manager,
            session_id,
            DeploymentEventType.HEALTH,
            health_result.summary,
            {"deploy_url": health_result.deploy_url},
        )

        if not health_result.success:

            return DeploymentPipelineResult(
                success=False,
                build=build_result,
                package=package_result,
                deploy=deploy_result,
                health=health_result,
                error_message=health_result.error_message,
                context=self._build_context(
                    build_result,
                    package_result,
                    deploy_result,
                    health_result,
                    None,
                ),
            )

        artifact_summary = "\n".join(
            f"- {a.name} ({a.type})"
            for a in artifact_manager.list()
        )

        release_result = self._release.release(
            workspace,
            project=project,
            archive_path=package_result.package_path,
            artifact_summary=artifact_summary,
        )

        self._register_release_artifacts(
            artifact_manager,
            project,
            release_result,
            package_result.artifacts,
        )

        self._save_memory(
            memory_manager,
            session_id,
            DeploymentEventType.RELEASE,
            f"Released {release_result.version} tag={release_result.tag}",
            {"version": release_result.version},
        )

        context = self._build_context(
            build_result,
            package_result,
            deploy_result,
            health_result,
            release_result,
        )

        return DeploymentPipelineResult(
            success=True,
            build=build_result,
            package=package_result,
            deploy=deploy_result,
            health=health_result,
            release=release_result,
            context=context,
            metadata={"version": release_result.version},
        )

    @staticmethod
    def _build_context(
        build_result,
        package_result,
        deploy_result,
        health_result,
        release_result,
    ) -> DeploymentContext:

        return DeploymentContext(
            build_summary=(
                f"success={build_result.success} "
                f"targets={len(build_result.sub_results)}"
            ),
            package_summary=(
                f"path={package_result.package_path} "
                f"type={package_result.package_type}"
            ),
            deploy_summary=(
                f"mode={deploy_result.mode.value} "
                f"url={deploy_result.deploy_url} "
                f"{deploy_result.message}"
            ),
            health_summary=health_result.summary,
            release_summary=(
                f"version={release_result.version} tag={release_result.tag}"
                if release_result
                else ""
            ),
            deploy_url=deploy_result.deploy_url,
            version=(
                release_result.version if release_result else ""
            ),
        )

    @staticmethod
    def _register_package_artifacts(
        artifact_manager: ArtifactManager,
        project: Project,
        package_result,
    ) -> None:

        workspace_path = Path(project.workspace_path)

        mappings = [
            ("Dockerfile", "Dockerfile", "deployment"),
            ("docker-compose.yml", "docker-compose.yml", "deployment"),
            ("deploy.sh", "deploy/deploy.sh", "deployment_script"),
        ]

        for name, relative, artifact_type in mappings:

            path = str(workspace_path / relative)

            artifact_manager.register_deployment_artifact(
                Artifact(
                    id=f"artifact_{uuid4().hex[:12]}",
                    name=name,
                    type=artifact_type,
                    path=path,
                    owner="DeploymentService",
                    metadata={
                        "stage": "deployment",
                        "package": package_result.package_path,
                    },
                )
            )

        if package_result.package_path:

            artifact_manager.register_deployment_artifact(
                Artifact(
                    id=f"artifact_{uuid4().hex[:12]}",
                    name="deployment.zip",
                    type="deployment_package",
                    path=package_result.package_path,
                    owner="DeploymentService",
                    metadata={"stage": "deployment"},
                )
            )

    @staticmethod
    def _register_release_artifacts(
        artifact_manager: ArtifactManager,
        project: Project,
        release_result,
        package_artifacts: list[str],
    ) -> None:

        if release_result.release_notes_path:

            artifact_manager.register_deployment_artifact(
                Artifact(
                    id=f"artifact_{uuid4().hex[:12]}",
                    name="RELEASE_NOTES.md",
                    type="release_notes",
                    path=release_result.release_notes_path,
                    owner="ReleaseManager",
                    metadata={
                        "version": release_result.version,
                        "tag": release_result.tag,
                    },
                )
            )

    @staticmethod
    def _save_memory(
        memory_manager: MemoryManager | None,
        session_id: str,
        event_type: DeploymentEventType,
        content: str,
        metadata: dict | None = None,
    ) -> None:

        if memory_manager is None or not session_id:

            return

        from app.memory.types import MemoryRecord

        record = MemoryRecord(
            role="assistant",
            content=content,
            metadata={
                "type": "memory",
                "category": event_type.value,
                **(metadata or {}),
            },
        )

        memory_manager.memory.save(session_id, record)
