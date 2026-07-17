from __future__ import annotations

import shutil
from pathlib import Path

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.deployment.deployment_result import DeployMode
from applications.software_team.deployment.deployment_result import DeployResult
from applications.software_team.execution.command_runner import CommandRunner


class DeployManager:
    """
    统一部署入口：Local / Docker / Remote（预留）。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        command_runner: CommandRunner | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._runner = command_runner or CommandRunner(
            timeout_seconds=self._settings.deployment_timeout_seconds,
        )

    def deploy(
        self,
        workspace: str | Path,
        *,
        project_name: str,
        mode: DeployMode | None = None,
    ) -> DeployResult:

        deploy_mode = mode or DeployMode(
            self._settings.deployment_mode,
        )

        if deploy_mode == DeployMode.LOCAL:

            return self._deploy_local(
                Path(workspace).resolve(),
                project_name,
            )

        if deploy_mode == DeployMode.DOCKER:

            return self._deploy_docker(
                Path(workspace).resolve(),
                project_name,
            )

        return DeployResult(
            success=True,
            workspace_path=str(workspace),
            mode=DeployMode.REMOTE,
            message="Remote deployment is reserved for future use.",
            metadata={"skipped": True},
        )

    def _deploy_local(
        self,
        workspace: Path,
        project_name: str,
    ) -> DeployResult:

        deploy_dir = workspace / "deploy"
        deploy_dir.mkdir(parents=True, exist_ok=True)

        port = self._settings.deployment_health_port
        start_script = deploy_dir / "start_local.sh"

        start_script.write_text(
            (
                f"#!/usr/bin/env bash\n"
                f"cd backend && "
                f"uvicorn main:app --host 0.0.0.0 --port {port}\n"
            ),
            encoding="utf-8",
        )

        url = f"http://localhost:{port}/api/health"

        return DeployResult(
            success=True,
            workspace_path=str(workspace),
            mode=DeployMode.LOCAL,
            message=(
                f"Local deployment prepared for {project_name}. "
                f"Run {start_script.name} to start."
            ),
            deploy_url=url,
            metadata={"start_script": str(start_script)},
        )

    def _deploy_docker(
        self,
        workspace: Path,
        project_name: str,
    ) -> DeployResult:

        if shutil.which("docker") is None:

            return DeployResult(
                success=False,
                workspace_path=str(workspace),
                mode=DeployMode.DOCKER,
                error_message="docker executable not found",
            )

        compose = workspace / "docker-compose.yml"

        if not compose.is_file():

            return DeployResult(
                success=False,
                workspace_path=str(workspace),
                mode=DeployMode.DOCKER,
                error_message="docker-compose.yml not found",
            )

        if not self._settings.deployment_run_docker:

            port = self._settings.deployment_health_port

            return DeployResult(
                success=True,
                workspace_path=str(workspace),
                mode=DeployMode.DOCKER,
                message="Docker deploy skipped (deployment_run_docker=false)",
                deploy_url=f"http://localhost:{port}/api/health",
                metadata={"skipped": True},
            )

        result = self._runner.run(
            command=["docker", "compose", "up", "-d", "--build"],
            cwd=workspace,
        )

        port = self._settings.deployment_health_port

        return DeployResult(
            success=result.success,
            workspace_path=str(workspace),
            mode=DeployMode.DOCKER,
            message=(
                "Docker deployment completed"
                if result.success
                else result.error_message
            ),
            deploy_url=f"http://localhost:{port}/api/health",
            stdout=result.stdout,
            stderr=result.stderr,
            error_message=result.error_message,
        )
