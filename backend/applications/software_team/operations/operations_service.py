from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.memory.manager import MemoryManager
from app.memory.types import MemoryRecord

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.operations.alert_manager import AlertManager
from applications.software_team.operations.diagnosis_manager import DiagnosisManager
from applications.software_team.operations.incident_manager import IncidentManager
from applications.software_team.operations.maintenance_manager import MaintenanceManager
from applications.software_team.operations.monitor_manager import MonitorManager
from applications.software_team.operations.operation_history import IncidentStatus
from applications.software_team.operations.operation_history import OperationContext
from applications.software_team.operations.operation_history import OperationEventType
from applications.software_team.operations.operation_history import OperationPipelineResult
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.artifact import Artifact
from applications.software_team.project.models.project import Project
from applications.software_team.project.workspace.workspace_manager import (
    WorkspaceManager,
)
from applications.software_team.runtime.team_agent_runtime import TeamAgentRuntime


class OperationsService:
    """
    运维流水线编排：Monitor → Alert → Incident → Diagnosis → Maintenance
    → Agent Fix → Verification → Redeploy。

    供 Coordinator 调用，Agent 不直接执行监控/部署命令。
    """

    REPORT_DIR = "operations"
    OPERATION_REPORT = "OPERATION_REPORT.md"

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        monitor_manager: MonitorManager | None = None,
        alert_manager: AlertManager | None = None,
        incident_manager: IncidentManager | None = None,
        diagnosis_manager: DiagnosisManager | None = None,
        maintenance_manager: MaintenanceManager | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._monitor = monitor_manager or MonitorManager(
            settings=self._settings,
        )
        self._alert = alert_manager or AlertManager(
            settings=self._settings,
        )
        self._incident = incident_manager or IncidentManager(
            settings=self._settings,
        )
        self._diagnosis = diagnosis_manager or DiagnosisManager(
            settings=self._settings,
        )
        self._maintenance = maintenance_manager or MaintenanceManager(
            settings=self._settings,
        )

    @property
    def enabled(self) -> bool:

        return self._settings.enable_operations

    def run_pipeline(
        self,
        project: Project,
        *,
        artifact_manager: ArtifactManager,
        workspace_manager: WorkspaceManager | None = None,
        memory_manager: MemoryManager | None = None,
        team_runtime: TeamAgentRuntime | None = None,
        team_prompt_builder=None,
        session_id: str = "",
        deploy_url: str = "",
        force_maintenance: bool = False,
    ) -> OperationPipelineResult:
        """
        执行完整运维流水线。
        """

        if not self.enabled:

            return OperationPipelineResult(
                success=True,
                metadata={"skipped": True},
            )

        workspace_manager = workspace_manager or WorkspaceManager(
            workspace_root=str(self._settings.workspace_root),
        )

        monitor_result = self._monitor.collect(
            project.workspace_path,
            deploy_url=deploy_url,
        )

        self._save_memory(
            memory_manager,
            session_id,
            OperationEventType.MONITOR,
            monitor_result.summary,
            {"healthy": monitor_result.success},
        )

        alert_result = self._alert.evaluate(monitor_result)

        error_rate_alert = self._alert.evaluate_error_rate(monitor_result)

        if error_rate_alert is not None:

            alert_result.alerts.append(error_rate_alert)
            alert_result.has_alerts = True

        self._save_memory(
            memory_manager,
            session_id,
            OperationEventType.ALERT,
            alert_result.summary,
            {"count": len(alert_result.alerts)},
        )

        deployment_history = self._load_deployment_history(
            memory_manager,
            session_id,
        )

        if not alert_result.has_alerts and not force_maintenance:

            context = OperationContext(
                monitor_summary=monitor_result.summary,
                alert_summary=alert_result.summary,
                deployment_history_summary=deployment_history,
            )

            report_path = self._write_operation_report(
                project.workspace_path,
                context,
                action_taken="No alerts — system healthy",
            )

            self._register_operation_artifacts(
                artifact_manager,
                project,
                report_path=report_path,
            )

            return OperationPipelineResult(
                success=True,
                monitor=monitor_result,
                alerts=alert_result,
                context=context,
                metadata={"healthy": True, "report": report_path},
            )

        incident_result = self._incident.create_from_alerts(
            project.workspace_path,
            alerts=alert_result.alerts,
            monitor=monitor_result,
        )

        if incident_result.incident is not None:

            self._incident.update_status(
                incident_result.incident,
                IncidentStatus.ANALYZING,
            )

            self._save_memory(
                memory_manager,
                session_id,
                OperationEventType.INCIDENT,
                incident_result.incident.title,
                {
                    "incident_id": incident_result.incident.id,
                    "impact": incident_result.incident.impact,
                },
            )

        diagnosis_result = self._diagnosis.analyze(
            project.workspace_path,
            incident=incident_result.incident,
            monitor=monitor_result,
            alerts=alert_result.alerts,
            memory_manager=memory_manager,
            session_id=session_id,
        )

        self._save_memory(
            memory_manager,
            session_id,
            OperationEventType.DIAGNOSIS,
            diagnosis_result.summary,
            {"causes": len(diagnosis_result.root_causes)},
        )

        tasks = self._maintenance.create_tasks(diagnosis_result)

        context = OperationContext(
            monitor_summary=monitor_result.summary,
            alert_summary=alert_result.summary,
            incident_summary=(
                incident_result.incident.title
                if incident_result.incident
                else ""
            ),
            diagnosis_summary=diagnosis_result.summary,
            maintenance_summary="\n".join(
                f"- {t.title}" for t in tasks
            ),
            deployment_history_summary=deployment_history,
        )

        runtime = team_runtime or TeamAgentRuntime(
            settings=self._settings,
        )

        maintenance_result = self._maintenance.execute(
            project,
            tasks=tasks,
            operation_context=context,
            artifact_manager=artifact_manager,
            workspace_manager=workspace_manager,
            team_runtime=runtime,
            team_prompt_builder=team_prompt_builder,
            session_id=session_id,
        )

        self._save_memory(
            memory_manager,
            session_id,
            OperationEventType.MAINTENANCE,
            f"Tasks={len(tasks)} fix={maintenance_result.success}",
            {
                "auto_fix": self._settings.operations_auto_fix,
                "verification": maintenance_result.verification_passed,
                "redeploy": maintenance_result.redeploy_success,
            },
        )

        if maintenance_result.redeploy_success:

            self._save_memory(
                memory_manager,
                session_id,
                OperationEventType.REDEPLOY,
                "Redeploy completed after maintenance",
                {},
            )

        if incident_result.incident is not None:

            final_status = (
                IncidentStatus.RESOLVED
                if maintenance_result.success
                else IncidentStatus.FIXING
            )

            self._incident.update_status(
                incident_result.incident,
                final_status,
            )

        report_path = self._write_operation_report(
            project.workspace_path,
            context,
            action_taken=(
                f"Maintenance executed: "
                f"verification={'PASS' if maintenance_result.verification_passed else 'FAIL'}, "
                f"redeploy={'OK' if maintenance_result.redeploy_success else 'SKIP'}"
            ),
        )

        self._register_operation_artifacts(
            artifact_manager,
            project,
            report_path=report_path,
            incident_report=incident_result.report_path,
            maintenance_report=maintenance_result.report_path,
        )

        success = (
            maintenance_result.success
            if self._settings.operations_auto_fix
            else True
        )

        return OperationPipelineResult(
            success=success,
            monitor=monitor_result,
            alerts=alert_result,
            incident=incident_result,
            diagnosis=diagnosis_result,
            maintenance=maintenance_result,
            context=context,
            error_message=(
                maintenance_result.error_message
                if not success
                else ""
            ),
            metadata={
                "incident_id": (
                    incident_result.incident.id
                    if incident_result.incident
                    else ""
                ),
                "task_count": len(tasks),
            },
        )

    def _write_operation_report(
        self,
        workspace: str | Path,
        context: OperationContext,
        *,
        action_taken: str,
    ) -> str:

        workspace_path = Path(workspace)
        report_dir = workspace_path / self.REPORT_DIR
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / self.OPERATION_REPORT

        content = f"""# Operation Report

{context.to_prompt_block()}

## Action Taken
{action_taken}

---
*Generated by OperationsService*
"""

        report_path.write_text(content, encoding=DEFAULT_ENCODING)

        return str(report_path)

    @staticmethod
    def _register_operation_artifacts(
        artifact_manager: ArtifactManager,
        project: Project,
        *,
        report_path: str = "",
        incident_report: str = "",
        maintenance_report: str = "",
    ) -> None:

        mappings = [
            (report_path, "OPERATION_REPORT.md", "operation_report"),
            (incident_report, "INCIDENT_REPORT.md", "incident_report"),
            (maintenance_report, "MAINTENANCE_REPORT.md", "maintenance_report"),
        ]

        for path, name, artifact_type in mappings:

            if not path:

                continue

            artifact_manager.register_operation_artifact(
                Artifact(
                    id=f"artifact_{uuid4().hex[:12]}",
                    name=name,
                    type=artifact_type,
                    path=path,
                    owner="OperationsService",
                    metadata={"stage": "operations"},
                )
            )

    @staticmethod
    def _load_deployment_history(
        memory_manager: MemoryManager | None,
        session_id: str,
    ) -> str:

        if memory_manager is None or not session_id:

            return ""

        context = memory_manager.load(session_id)
        lines: list[str] = []

        for record in context.records:

            category = record.metadata.get("category", "")

            if category in (
                "deployment_history",
                "build_history",
                "release_history",
                "health_check",
            ):

                lines.append(f"- [{category}] {record.content[:120]}")

        return "\n".join(lines[-10:]) if lines else "No deployment history in session"

    @staticmethod
    def _save_memory(
        memory_manager: MemoryManager | None,
        session_id: str,
        event_type: OperationEventType,
        content: str,
        metadata: dict | None = None,
    ) -> None:

        if memory_manager is None or not session_id:

            return

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
