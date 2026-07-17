from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.deployment.deployment_result import PackageResult


class PackageManager:
    """
    生成交付产物：Dockerfile、docker-compose、Zip 包。
    """

    DEPLOY_DIR = "deploy"

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()

    def package(
        self,
        workspace: str | Path,
        *,
        project_name: str,
    ) -> PackageResult:

        workspace_path = Path(workspace).resolve()
        deploy_dir = workspace_path / self.DEPLOY_DIR
        deploy_dir.mkdir(parents=True, exist_ok=True)

        artifacts: list[str] = []

        dockerfile = self._ensure_dockerfile(
            workspace_path,
            project_name,
        )

        artifacts.append(str(dockerfile))

        compose = self._ensure_docker_compose(
            workspace_path,
            project_name,
        )

        artifacts.append(str(compose))

        deploy_script = self._ensure_deploy_script(
            deploy_dir,
            project_name,
        )

        artifacts.append(str(deploy_script))

        zip_path = self._create_zip_package(
            workspace_path,
            project_name,
        )

        artifacts.append(str(zip_path))

        return PackageResult(
            success=True,
            workspace_path=str(workspace_path),
            package_path=str(zip_path),
            package_type="zip",
            artifacts=artifacts,
            metadata={
                "dockerfile": str(dockerfile),
                "compose": str(compose),
                "deploy_script": str(deploy_script),
            },
        )

    def _ensure_dockerfile(
        self,
        workspace: Path,
        project_name: str,
    ) -> Path:

        dockerfile = workspace / "Dockerfile"

        if dockerfile.is_file():

            return dockerfile

        backend = workspace / "backend"
        has_backend = (backend / "main.py").is_file()

        if has_backend:

            content = f'''FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE {self._settings.deployment_health_port}
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{self._settings.deployment_health_port}"]
'''

        else:

            content = f'''FROM nginx:alpine
COPY frontend/ /usr/share/nginx/html/
EXPOSE 80
'''

        dockerfile.write_text(content, encoding=DEFAULT_ENCODING)

        return dockerfile

    def _ensure_docker_compose(
        self,
        workspace: Path,
        project_name: str,
    ) -> Path:

        compose_path = workspace / "docker-compose.yml"

        if compose_path.is_file():

            return compose_path

        slug = project_name.lower().replace(" ", "-")[:30]
        port = self._settings.deployment_health_port

        content = f'''services:
  app:
    build: .
    container_name: {slug}
    ports:
      - "{port}:{port}"
    restart: unless-stopped
'''

        compose_path.write_text(content, encoding=DEFAULT_ENCODING)

        return compose_path

    def _ensure_deploy_script(
        self,
        deploy_dir: Path,
        project_name: str,
    ) -> Path:

        script = deploy_dir / "deploy.sh"
        port = self._settings.deployment_health_port

        content = f'''#!/usr/bin/env bash
set -euo pipefail
echo "Deploying {project_name}..."
docker compose up -d --build
echo "Deployed. Health: http://localhost:{port}/api/health"
'''

        script.write_text(content, encoding=DEFAULT_ENCODING)

        return script

    def _create_zip_package(
        self,
        workspace: Path,
        project_name: str,
    ) -> Path:

        output_dir = workspace / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        slug = project_name.lower().replace(" ", "-")[:30]
        zip_path = output_dir / f"{slug}-deployment.zip"

        include_dirs = (
            "backend",
            "frontend",
            "docs",
            "tests",
            "deploy",
        )

        include_files = (
            "README.md",
            "Dockerfile",
            "docker-compose.yml",
        )

        with zipfile.ZipFile(
            zip_path,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as archive:

            for name in include_files:

                file_path = workspace / name

                if file_path.is_file():

                    archive.write(
                        file_path,
                        arcname=name,
                    )

            for directory in include_dirs:

                dir_path = workspace / directory

                if not dir_path.is_dir():

                    continue

                for file_path in dir_path.rglob("*"):

                    if file_path.is_file():

                        archive.write(
                            file_path,
                            arcname=str(
                                file_path.relative_to(workspace)
                            ),
                        )

        return zip_path
