from __future__ import annotations

from pathlib import Path

from app.memory.manager import MemoryManager

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.operations.operation_history import Alert
from applications.software_team.operations.operation_history import DiagnosisResult
from applications.software_team.operations.operation_history import Incident
from applications.software_team.operations.operation_history import MonitorResult


class DiagnosisManager:
    """
    分析日志、异常、Health Result、Verification History，定位可能原因。
    """

    _VERIFICATION_CATEGORIES = frozenset({
        "fix_attempt",
        "deployment_history",
        "build_history",
        "health_check",
    })

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()

    def analyze(
        self,
        workspace: str | Path,
        *,
        incident: Incident | None = None,
        monitor: MonitorResult | None = None,
        alerts: list[Alert] | None = None,
        memory_manager: MemoryManager | None = None,
        session_id: str = "",
    ) -> DiagnosisResult:

        workspace_path = Path(workspace).resolve()
        root_causes: list[str] = []
        evidence: list[str] = []
        recommendations: list[str] = []

        if monitor is not None:

            for metric in monitor.metrics:

                if not metric.success and not metric.metadata.get("skipped"):

                    evidence.append(
                        f"Monitor [{metric.name}]: {metric.message}"
                    )

                    cause = self._map_metric_to_cause(metric.name)

                    if cause and cause not in root_causes:

                        root_causes.append(cause)

        if alerts:

            for alert in alerts:

                evidence.append(
                    f"Alert [{alert.alert_type}]: {alert.message}"
                )

                cause = self._map_alert_to_cause(alert.alert_type)

                if cause and cause not in root_causes:

                    root_causes.append(cause)

        if incident is not None and incident.logs:

            log_hints = self._analyze_logs(incident.logs)

            evidence.extend(log_hints["evidence"])
            root_causes.extend(
                c for c in log_hints["causes"] if c not in root_causes
            )

        memory_hints = self._analyze_memory(
            memory_manager,
            session_id,
        )

        evidence.extend(memory_hints["evidence"])
        root_causes.extend(
            c for c in memory_hints["causes"] if c not in root_causes
        )

        recommendations = self._build_recommendations(
            root_causes,
            workspace_path,
        )

        if not root_causes:

            root_causes.append("Unable to determine root cause from available data")

        return DiagnosisResult(
            success=True,
            root_causes=root_causes,
            evidence=evidence,
            recommendations=recommendations,
            metadata={
                "workspace": str(workspace_path),
                "incident_id": incident.id if incident else "",
            },
        )

    @staticmethod
    def _map_metric_to_cause(metric_name: str) -> str:

        mapping = {
            "api_status": "Application API is down or misconfigured",
            "health_check": "Post-deploy health validation failed",
            "service_status": "Deployment artifacts missing or incomplete",
            "database": "Database connectivity or schema issue",
            "cpu": "High CPU load may cause timeouts",
            "memory": "Memory pressure may cause OOM or slow responses",
            "disk": "Insufficient disk space",
        }

        return mapping.get(metric_name, "")

    @staticmethod
    def _map_alert_to_cause(alert_type: str) -> str:

        mapping = {
            "service_unavailable": "Service is not running or not reachable",
            "response_time": "Performance degradation — slow API responses",
            "health_check_failed": "Health endpoint returning errors",
            "error_rate": "Elevated failure rate across monitored metrics",
            "database_error": "Database layer failure",
            "service_degraded": "Partial deployment or missing components",
        }

        return mapping.get(alert_type, "")

    @staticmethod
    def _analyze_logs(logs: str) -> dict[str, list[str]]:

        causes: list[str] = []
        evidence: list[str] = []

        keywords = {
            "traceback": "Unhandled exception in application code",
            "connection refused": "Service not listening on expected port",
            "timeout": "Network or dependency timeout",
            "404": "Missing API route or incorrect path",
            "500": "Internal server error in backend",
            "modulenotfounderror": "Missing Python dependency",
            "importerror": "Import failure in backend module",
        }

        lower_logs = logs.lower()

        for keyword, cause in keywords.items():

            if keyword in lower_logs:

                evidence.append(f"Log keyword detected: {keyword}")
                causes.append(cause)

        return {"causes": causes, "evidence": evidence}

    def _analyze_memory(
        self,
        memory_manager: MemoryManager | None,
        session_id: str,
    ) -> dict[str, list[str]]:

        causes: list[str] = []
        evidence: list[str] = []

        if memory_manager is None or not session_id:

            return {"causes": causes, "evidence": evidence}

        context = memory_manager.load(session_id)

        for record in context.records:

            category = record.metadata.get("category", "")

            if category not in self._VERIFICATION_CATEGORIES:

                continue

            snippet = record.content[:200]

            evidence.append(f"Memory [{category}]: {snippet}")

            if category == "fix_attempt":

                causes.append("Previous fix attempts did not fully resolve the issue")

            if category == "health_check":

                causes.append("Historical health check failures detected")

            if category == "deployment_history":

                causes.append("Recent deployment may have introduced regression")

        return {"causes": causes, "evidence": evidence}

    @staticmethod
    def _build_recommendations(
        root_causes: list[str],
        workspace: Path,
    ) -> list[str]:

        recommendations: list[str] = []

        if any("API" in c or "Service" in c for c in root_causes):

            recommendations.append(
                "Verify service is running and health endpoint responds"
            )
            recommendations.append(
                "Check deploy/start scripts in deploy/ directory"
            )

        if any("Database" in c or "database" in c for c in root_causes):

            recommendations.append(
                "Validate database file permissions and connection string"
            )

        if any("Performance" in c or "CPU" in c or "Memory" in c for c in root_causes):

            recommendations.append(
                "Profile hot paths and consider caching or query optimization"
            )

        if any("exception" in c.lower() or "Import" in c for c in root_causes):

            backend = workspace / "backend"

            if backend.is_dir():

                recommendations.append(
                    "Run BackendAgent fix on backend/ with error context"
                )

        if not recommendations:

            recommendations.append(
                "Review incident logs and re-run verification on backend"
            )

        return recommendations
