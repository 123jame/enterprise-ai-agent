"""
P9 Operations & Monitoring 测试。

运行:
    cd backend
    python -m applications.software_team.tests.test_operations
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.memory.manager import MemoryManager

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.operations.alert_manager import AlertManager
from applications.software_team.operations.diagnosis_manager import DiagnosisManager
from applications.software_team.operations.incident_manager import IncidentManager
from applications.software_team.operations.maintenance_manager import MaintenanceManager
from applications.software_team.operations.monitor_manager import MonitorManager
from applications.software_team.operations.operation_history import Alert
from applications.software_team.operations.operation_history import AlertSeverity
from applications.software_team.operations.operation_history import MetricSnapshot
from applications.software_team.operations.operation_history import MonitorResult
from applications.software_team.operations.operation_history import OperationContext
from applications.software_team.operations.operations_service import OperationsService
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.project import Project
from applications.software_team.project.models.project_status import ProjectStatus


def _create_workspace(root: Path, *, healthy: bool = True) -> None:

    root.mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text("# ops test\n", encoding="utf-8")

    backend = root / "backend"
    backend.mkdir(parents=True, exist_ok=True)
    (backend / "main.py").write_text("app = object()\n", encoding="utf-8")

    if healthy:

        (root / "Dockerfile").write_text("FROM python:3.11-slim\n", encoding="utf-8")
        (root / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
        deploy = root / "deploy"
        deploy.mkdir(exist_ok=True)
        (deploy / "deploy.sh").write_text("#!/bin/bash\n", encoding="utf-8")


def test_monitor_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _create_workspace(root)

        settings = SoftwareTeamSettings(
            operations_monitor_http=False,
        )
        result = MonitorManager(settings=settings).collect(root)

        assert result.success is True
        assert len(result.metrics) >= 4
        names = {m.name for m in result.metrics}
        assert "health_check" in names
        assert "service_status" in names
        print("MonitorManager: PASS")


def test_alert_manager() -> None:

    monitor = MonitorResult(
        success=False,
        workspace_path="/tmp",
        metrics=[
            MetricSnapshot(
                name="api_status",
                value=5000,
                unit="ms",
                success=False,
                message="API unreachable",
            ),
            MetricSnapshot(
                name="health_check",
                value=0.0,
                success=False,
                message="Health FAIL",
            ),
        ],
    )

    settings = SoftwareTeamSettings(
        operations_alert_response_time_ms=3000,
    )
    result = AlertManager(settings=settings).evaluate(monitor)

    assert result.has_alerts is True
    assert len(result.alerts) >= 2
    print("AlertManager: PASS")


def test_incident_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _create_workspace(root, healthy=False)

        alerts = [
            Alert.create(
                alert_type="health_check_failed",
                severity=AlertSeverity.CRITICAL,
                message="Health check failed",
            )
        ]

        monitor = MonitorManager(
            settings=SoftwareTeamSettings(operations_monitor_http=False),
        ).collect(root)

        result = IncidentManager().create_from_alerts(
            root,
            alerts=alerts,
            monitor=monitor,
        )

        assert result.success is True
        assert result.incident is not None
        assert Path(result.report_path).is_file()
        print("IncidentManager: PASS")


def test_diagnosis_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _create_workspace(root, healthy=False)

        alerts = [
            Alert.create(
                alert_type="service_degraded",
                severity=AlertSeverity.WARNING,
                message="Missing deployment files",
            )
        ]

        incident_result = IncidentManager().create_from_alerts(
            root,
            alerts=alerts,
        )

        result = DiagnosisManager().analyze(
            root,
            incident=incident_result.incident,
            alerts=alerts,
        )

        assert result.success is True
        assert result.root_causes
        assert result.recommendations
        print("DiagnosisManager: PASS")


def test_maintenance_manager_create_tasks() -> None:

    from applications.software_team.operations.operation_history import (
        DiagnosisResult,
    )

    diagnosis = DiagnosisResult(
        success=True,
        root_causes=[
            "Application API is down or misconfigured",
            "High CPU load may cause timeouts",
        ],
        recommendations=["Restart service", "Profile backend"],
    )

    tasks = MaintenanceManager().create_tasks(diagnosis)

    assert len(tasks) >= 2
    assert tasks[0].target_agent == "BackendAgent"
    print("MaintenanceManager (create): PASS")


def test_operations_service_healthy() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _create_workspace(root, healthy=True)

        project = Project(
            id="p1",
            name="Ops Demo",
            requirement="ops",
            workspace_path=str(root),
            status=ProjectStatus.FINISHED,
        )

        settings = SoftwareTeamSettings(
            enable_operations=True,
            operations_monitor_http=False,
            operations_auto_fix=False,
        )

        service = OperationsService(settings=settings)
        memory = MemoryManager()
        artifact_manager = ArtifactManager()

        result = service.run_pipeline(
            project,
            artifact_manager=artifact_manager,
            memory_manager=memory,
            session_id="ops-healthy",
        )

        assert result.success is True
        assert result.metadata.get("healthy") is True
        assert result.monitor is not None

        ops_artifacts = artifact_manager.find_operation_artifacts()
        assert len(ops_artifacts) >= 1

        memory_context = memory.load("ops-healthy")
        categories = {
            r.metadata.get("category")
            for r in memory_context.records
        }
        assert "operation_history" in categories

        print("OperationsService (healthy): PASS")


def test_operations_service_with_alerts() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _create_workspace(root, healthy=False)

        project = Project(
            id="p2",
            name="Ops Alert",
            requirement="ops",
            workspace_path=str(root),
            status=ProjectStatus.FINISHED,
        )

        settings = SoftwareTeamSettings(
            enable_operations=True,
            operations_monitor_http=False,
            operations_auto_fix=False,
        )

        service = OperationsService(settings=settings)
        artifact_manager = ArtifactManager()
        memory = MemoryManager()

        result = service.run_pipeline(
            project,
            artifact_manager=artifact_manager,
            memory_manager=memory,
            session_id="ops-alert",
        )

        assert result.success is True
        assert result.alerts is not None
        assert result.alerts.has_alerts is True
        assert result.incident is not None
        assert result.diagnosis is not None
        assert result.maintenance is not None

        memory_context = memory.load("ops-alert")
        categories = {
            r.metadata.get("category")
            for r in memory_context.records
        }
        assert "incident_history" in categories
        assert "maintenance_history" in categories

        ops_artifacts = artifact_manager.find_operation_artifacts()
        assert len(ops_artifacts) >= 2

        print("OperationsService (alerts): PASS")


def test_team_prompt_builder_operation_context() -> None:

    from app.agents.types import AgentContext

    from applications.software_team.agents.base.coordinator_context import (
        CoordinatorContext,
    )
    from applications.software_team.prompt.team_prompt_builder import (
        TeamPromptBuilder,
    )

    project = Project(
        id="p1",
        name="Demo",
        requirement="ops",
        workspace_path="/tmp/ws",
        status=ProjectStatus.FINISHED,
    )

    context = CoordinatorContext.from_agent_context(
        context=AgentContext(
            session_id="s1",
            user_message="fix production",
            metadata={"operations_mode": True},
        ),
        project=project,
    )

    ops_ctx = OperationContext(
        monitor_summary="Monitor: FAIL",
        alert_summary="Alerts: 1\n- [critical] health_check_failed",
        incident_summary="Health check failed",
        diagnosis_summary="Root causes:\n- Health endpoint returning errors",
        deployment_history_summary="- [deployment_history] Deploy ok",
    )

    builder = TeamPromptBuilder()
    messages = builder.build(
        "ProductAgent",
        context,
        ArtifactManager(),
        operation_context=ops_ctx,
    )

    combined = "\n".join(m.content for m in messages)
    assert "Operation Context" in combined
    assert "health_check_failed" in combined
    print("TeamPromptBuilder operations: PASS")


def test_coordinator_run_operations() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        _create_workspace(root, healthy=True)

        settings = SoftwareTeamSettings(
            enable_operations=True,
            operations_monitor_http=False,
        )

        from applications.software_team.coordinator.coordinator import (
            SoftwareTeamCoordinator,
        )

        coordinator = SoftwareTeamCoordinator(settings=settings)

        result = coordinator.run_operations(
            session_id="coord-ops",
            workspace_path=str(root),
        )

        assert result.success is True
        assert "healthy" in result.content.lower() or "Operations" in result.content
        print("Coordinator run_operations: PASS")


def main() -> None:

    test_monitor_manager()
    test_alert_manager()
    test_incident_manager()
    test_diagnosis_manager()
    test_maintenance_manager_create_tasks()
    test_operations_service_healthy()
    test_operations_service_with_alerts()
    test_team_prompt_builder_operation_context()
    test_coordinator_run_operations()
    print("\nAll P9 operations tests passed.")


if __name__ == "__main__":

    main()
