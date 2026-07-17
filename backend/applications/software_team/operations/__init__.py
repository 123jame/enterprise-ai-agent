from applications.software_team.operations.operation_history import Alert
from applications.software_team.operations.operation_history import AlertResult
from applications.software_team.operations.operation_history import AlertSeverity
from applications.software_team.operations.operation_history import DiagnosisResult
from applications.software_team.operations.operation_history import Incident
from applications.software_team.operations.operation_history import IncidentResult
from applications.software_team.operations.operation_history import IncidentStatus
from applications.software_team.operations.operation_history import MaintenanceResult
from applications.software_team.operations.operation_history import MaintenanceTask
from applications.software_team.operations.operation_history import MaintenanceTaskType
from applications.software_team.operations.operation_history import MetricSnapshot
from applications.software_team.operations.operation_history import MonitorResult
from applications.software_team.operations.operation_history import OperationContext
from applications.software_team.operations.operation_history import OperationEventType
from applications.software_team.operations.operation_history import OperationPipelineResult

__all__ = [
    "Alert",
    "AlertManager",
    "AlertResult",
    "AlertSeverity",
    "DiagnosisManager",
    "DiagnosisResult",
    "Incident",
    "IncidentManager",
    "IncidentResult",
    "IncidentStatus",
    "MaintenanceManager",
    "MaintenanceResult",
    "MaintenanceTask",
    "MaintenanceTaskType",
    "MetricSnapshot",
    "MonitorManager",
    "MonitorResult",
    "OperationContext",
    "OperationEventType",
    "OperationPipelineResult",
    "OperationsService",
]


def __getattr__(name: str):
    """
    延迟导入 Manager，避免与 agents/prompt 循环依赖。
    """

    if name == "AlertManager":
        from applications.software_team.operations.alert_manager import AlertManager

        return AlertManager

    if name == "DiagnosisManager":
        from applications.software_team.operations.diagnosis_manager import (
            DiagnosisManager,
        )

        return DiagnosisManager

    if name == "IncidentManager":
        from applications.software_team.operations.incident_manager import (
            IncidentManager,
        )

        return IncidentManager

    if name == "MaintenanceManager":
        from applications.software_team.operations.maintenance_manager import (
            MaintenanceManager,
        )

        return MaintenanceManager

    if name == "MonitorManager":
        from applications.software_team.operations.monitor_manager import (
            MonitorManager,
        )

        return MonitorManager

    if name == "OperationsService":
        from applications.software_team.operations.operations_service import (
            OperationsService,
        )

        return OperationsService

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
