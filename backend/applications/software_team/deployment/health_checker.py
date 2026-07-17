from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.deployment.deployment_result import HealthResult
from applications.software_team.execution.command_runner import CommandRunner


class HealthChecker:
    """
    部署后健康检查。
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

    def check(
        self,
        workspace: str | Path,
        *,
        deploy_url: str = "",
    ) -> HealthResult:

        workspace_path = Path(workspace).resolve()
        checks: list[dict[str, str | bool]] = []

        checks.append(
            self._check_structure(workspace_path)
        )

        backend = workspace_path / "backend"

        if (backend / "main.py").is_file():

            checks.append(
                self._check_backend_import(backend)
            )

        url = deploy_url or (
            f"http://localhost:"
            f"{self._settings.deployment_health_port}/api/health"
        )

        if self._settings.deployment_health_http:

            checks.append(
                self._check_http(url)
            )

        failed = [c for c in checks if not c.get("success")]

        return HealthResult(
            success=len(failed) == 0,
            workspace_path=str(workspace_path),
            checks=checks,
            deploy_url=url,
            error_message="; ".join(
                str(c.get("message", ""))
                for c in failed
            ),
            metadata={"check_count": len(checks)},
        )

    def _check_structure(
        self,
        workspace: Path,
    ) -> dict[str, str | bool]:

        required = ["README.md", "Dockerfile"]

        missing = [
            name
            for name in required
            if not (workspace / name).is_file()
        ]

        return {
            "name": "structure",
            "success": len(missing) == 0,
            "message": (
                "Deployment structure ok"
                if not missing
                else f"Missing: {', '.join(missing)}"
            ),
        }

    def _check_backend_import(
        self,
        backend: Path,
    ) -> dict[str, str | bool]:

        result = self._runner.run(
            command=[
                sys.executable,
                "-c",
                "from main import app; print('ok')",
            ],
            cwd=backend,
        )

        return {
            "name": "backend_import",
            "success": result.success,
            "message": (
                "Backend import ok"
                if result.success
                else result.error_message
            ),
        }

    def _check_http(
        self,
        url: str,
    ) -> dict[str, str | bool]:

        try:

            request = urllib.request.Request(
                url,
                method="GET",
            )

            with urllib.request.urlopen(
                request,
                timeout=self._settings.deployment_health_timeout,
            ) as response:

                body = response.read().decode("utf-8", errors="replace")

                success = response.status == 200

                return {
                    "name": "http_health",
                    "success": success,
                    "message": (
                        f"HTTP {response.status}: {body[:200]}"
                        if success
                        else f"HTTP {response.status}"
                    ),
                }

        except urllib.error.URLError as error:

            return {
                "name": "http_health",
                "success": False,
                "message": (
                    f"HTTP check skipped/unreachable: {error}"
                ),
            }

        except OSError as error:

            return {
                "name": "http_health",
                "success": False,
                "message": str(error),
            }
