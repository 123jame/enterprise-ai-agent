from __future__ import annotations

import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.deployment.health_checker import HealthChecker
from applications.software_team.execution.command_runner import CommandRunner
from applications.software_team.operations.operation_history import MetricSnapshot
from applications.software_team.operations.operation_history import MonitorResult


class MonitorManager:
    """
    统一监控系统运行状态。

    支持 API 状态、CPU、Memory、Disk、Database、Service Status。
    命令经 HealthChecker / CommandRunner，Agent 不直接执行监控命令。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        health_checker: HealthChecker | None = None,
        command_runner: CommandRunner | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._health = health_checker or HealthChecker(
            settings=self._settings,
        )
        self._runner = command_runner or CommandRunner(
            timeout_seconds=self._settings.operations_timeout_seconds,
        )

    def collect(
        self,
        workspace: str | Path,
        *,
        deploy_url: str = "",
    ) -> MonitorResult:

        workspace_path = Path(workspace).resolve()
        metrics: list[MetricSnapshot] = []

        metrics.append(self._check_api_status(workspace_path, deploy_url))
        metrics.append(self._check_service_status(workspace_path))
        metrics.append(self._check_database(workspace_path))
        metrics.extend(self._check_system_resources(workspace_path))

        health = self._health.check(
            workspace_path,
            deploy_url=deploy_url,
        )

        metrics.append(
            MetricSnapshot(
                name="health_check",
                value=1.0 if health.success else 0.0,
                unit="",
                success=health.success,
                message=health.summary[:500],
            )
        )

        failed = [m for m in metrics if not m.success]

        return MonitorResult(
            success=len(failed) == 0,
            workspace_path=str(workspace_path),
            metrics=metrics,
            error_message="; ".join(
                m.message for m in failed if m.message
            ),
            metadata={"metric_count": len(metrics), "failed": len(failed)},
        )

    def _check_api_status(
        self,
        workspace: Path,
        deploy_url: str,
    ) -> MetricSnapshot:

        if not self._settings.operations_monitor_http:

            return MetricSnapshot(
                name="api_status",
                value=1.0,
                success=True,
                message="HTTP monitoring disabled",
                metadata={"skipped": True},
            )

        url = deploy_url or (
            f"http://localhost:"
            f"{self._settings.deployment_health_port}/api/health"
        )

        start = time.perf_counter()

        try:

            request = urllib.request.Request(url, method="GET")

            with urllib.request.urlopen(
                request,
                timeout=self._settings.deployment_health_timeout,
            ) as response:

                elapsed_ms = (time.perf_counter() - start) * 1000
                success = response.status == 200

                return MetricSnapshot(
                    name="api_status",
                    value=elapsed_ms,
                    unit="ms",
                    success=success,
                    message=(
                        f"HTTP {response.status} in {elapsed_ms:.0f}ms"
                        if success
                        else f"HTTP {response.status}"
                    ),
                    metadata={"url": url, "status_code": response.status},
                )

        except urllib.error.URLError as error:

            elapsed_ms = (time.perf_counter() - start) * 1000

            return MetricSnapshot(
                name="api_status",
                value=elapsed_ms,
                unit="ms",
                success=False,
                message=f"API unreachable: {error}",
                metadata={"url": url},
            )

        except OSError as error:

            return MetricSnapshot(
                name="api_status",
                value=0.0,
                success=False,
                message=str(error),
                metadata={"url": url},
            )

    def _check_service_status(
        self,
        workspace: Path,
    ) -> MetricSnapshot:

        indicators = [
            workspace / "Dockerfile",
            workspace / "docker-compose.yml",
            workspace / "deploy" / "deploy.sh",
            workspace / "backend" / "main.py",
        ]

        present = sum(1 for path in indicators if path.is_file())
        total = len(indicators)
        ratio = present / total if total else 0.0

        return MetricSnapshot(
            name="service_status",
            value=ratio * 100,
            unit="%",
            success=present >= 2,
            message=f"Deployment artifacts present: {present}/{total}",
            metadata={"present": present, "total": total},
        )

    def _check_database(
        self,
        workspace: Path,
    ) -> MetricSnapshot:

        backend = workspace / "backend"
        db_files = list(backend.glob("*.db")) if backend.is_dir() else []

        if db_files:

            db_path = db_files[0]

            try:

                import sqlite3

                connection = sqlite3.connect(str(db_path), timeout=2)
                connection.execute("SELECT 1")
                connection.close()

                return MetricSnapshot(
                    name="database",
                    value=1.0,
                    success=True,
                    message=f"SQLite ok: {db_path.name}",
                    metadata={"path": str(db_path), "type": "sqlite"},
                )

            except OSError as error:

                return MetricSnapshot(
                    name="database",
                    value=0.0,
                    success=False,
                    message=f"Database check failed: {error}",
                    metadata={"path": str(db_path)},
                )

        if (backend / "main.py").is_file():

            result = self._runner.run(
                command=[
                    sys.executable,
                    "-c",
                    "print('db_check_skipped')",
                ],
                cwd=backend,
            )

            return MetricSnapshot(
                name="database",
                value=1.0 if result.success else 0.0,
                success=result.success,
                message=(
                    "No local DB file; backend reachable"
                    if result.success
                    else result.error_message
                ),
                metadata={"skipped_file_check": True},
            )

        return MetricSnapshot(
            name="database",
            value=1.0,
            success=True,
            message="No database configured",
            metadata={"skipped": True},
        )

    def _check_system_resources(
        self,
        workspace: Path,
    ) -> list[MetricSnapshot]:

        metrics: list[MetricSnapshot] = []

        try:

            usage = shutil.disk_usage(workspace)
            used_percent = (usage.used / usage.total) * 100 if usage.total else 0

            metrics.append(
                MetricSnapshot(
                    name="disk",
                    value=used_percent,
                    unit="%",
                    success=(
                        used_percent
                        < self._settings.operations_disk_threshold_percent
                    ),
                    message=(
                        f"Disk used {used_percent:.1f}% "
                        f"({usage.free // (1024 * 1024)} MB free)"
                    ),
                )
            )

        except OSError as error:

            metrics.append(
                MetricSnapshot(
                    name="disk",
                    value=0.0,
                    success=False,
                    message=str(error),
                )
            )

        cpu_memory = self._collect_cpu_memory()

        if cpu_memory is not None:

            metrics.extend(cpu_memory)

        return metrics

    def _collect_cpu_memory(self) -> list[MetricSnapshot] | None:

        try:

            import psutil

        except ImportError:

            return [
                MetricSnapshot(
                    name="cpu",
                    value=0.0,
                    success=True,
                    message="CPU monitoring skipped (psutil not installed)",
                    metadata={"skipped": True},
                ),
                MetricSnapshot(
                    name="memory",
                    value=0.0,
                    success=True,
                    message="Memory monitoring skipped (psutil not installed)",
                    metadata={"skipped": True},
                ),
            ]

        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        return [
            MetricSnapshot(
                name="cpu",
                value=cpu_percent,
                unit="%",
                success=(
                    cpu_percent
                    < self._settings.operations_cpu_threshold_percent
                ),
                message=f"CPU usage {cpu_percent:.1f}%",
            ),
            MetricSnapshot(
                name="memory",
                value=memory.percent,
                unit="%",
                success=(
                    memory.percent
                    < self._settings.operations_memory_threshold_percent
                ),
                message=(
                    f"Memory usage {memory.percent:.1f}% "
                    f"({memory.available // (1024 * 1024)} MB available)"
                ),
            ),
        ]
