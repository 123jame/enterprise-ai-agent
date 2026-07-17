from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class OperationEventType(str, Enum):
    """
    Memory 运维事件类型。
    """

    MONITOR = "operation_history"
    ALERT = "operation_history"
    INCIDENT = "incident_history"
    DIAGNOSIS = "operation_history"
    MAINTENANCE = "maintenance_history"
    REDEPLOY = "operation_history"


class IncidentStatus(str, Enum):
    """
    故障处理状态。
    """

    OPEN = "open"
    ANALYZING = "analyzing"
    FIXING = "fixing"
    RESOLVED = "resolved"
    CLOSED = "closed"


class MaintenanceTaskType(str, Enum):
    """
    维护任务类型。
    """

    BUG_FIX = "bug_fix"
    PERFORMANCE = "performance_optimization"
    SECURITY = "security_patch"
    GENERAL = "general_maintenance"


class AlertSeverity(str, Enum):
    """
    告警级别。
    """

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricSnapshot:
    """
    单项监控指标快照。
    """

    name: str
    value: float
    unit: str = ""
    success: bool = True
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitorResult:
    """
    监控采集结果。
    """

    success: bool
    workspace_path: str
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
    )
    metrics: list[MetricSnapshot] = field(default_factory=list)
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def summary(self) -> str:

        lines = [f"Monitor: {'OK' if self.success else 'FAIL'}"]

        for metric in self.metrics:

            status = "OK" if metric.success else "FAIL"
            lines.append(
                f"- [{status}] {metric.name}: "
                f"{metric.value}{metric.unit} — {metric.message}"
            )

        return "\n".join(lines)


@dataclass
class Alert:
    """
    单条告警。
    """

    id: str
    alert_type: str
    severity: AlertSeverity
    message: str
    metric_name: str = ""
    threshold: float = 0.0
    actual_value: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        alert_type: str,
        severity: AlertSeverity,
        message: str,
        metric_name: str = "",
        threshold: float = 0.0,
        actual_value: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> Alert:

        return cls(
            id=f"alert_{uuid4().hex[:12]}",
            alert_type=alert_type,
            severity=severity,
            message=message,
            metric_name=metric_name,
            threshold=threshold,
            actual_value=actual_value,
            metadata=metadata or {},
        )


@dataclass
class AlertResult:
    """
    告警评估结果。
    """

    success: bool
    has_alerts: bool
    alerts: list[Alert] = field(default_factory=list)
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def summary(self) -> str:

        if not self.has_alerts:

            return "Alerts: none"

        lines = [f"Alerts: {len(self.alerts)}"]

        for alert in self.alerts:

            lines.append(
                f"- [{alert.severity.value}] {alert.alert_type}: "
                f"{alert.message}"
            )

        return "\n".join(lines)


@dataclass
class Incident:
    """
    故障事件记录。
    """

    id: str
    title: str
    status: IncidentStatus
    occurred_at: str
    impact: str
    logs: str
    alerts: list[Alert] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        title: str,
        impact: str,
        logs: str,
        alerts: list[Alert] | None = None,
        status: IncidentStatus = IncidentStatus.OPEN,
        metadata: dict[str, Any] | None = None,
    ) -> Incident:

        return cls(
            id=f"incident_{uuid4().hex[:12]}",
            title=title,
            status=status,
            occurred_at=datetime.utcnow().isoformat() + "Z",
            impact=impact,
            logs=logs,
            alerts=alerts or [],
            metadata=metadata or {},
        )


@dataclass
class IncidentResult:
    """
    Incident 创建/更新结果。
    """

    success: bool
    incident: Incident | None = None
    report_path: str = ""
    error_message: str = ""


@dataclass
class DiagnosisResult:
    """
    故障诊断结果。
    """

    success: bool
    root_causes: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def summary(self) -> str:

        lines = ["Diagnosis:"]

        if self.root_causes:

            lines.append("Root causes:")
            lines.extend(f"- {cause}" for cause in self.root_causes)

        if self.recommendations:

            lines.append("Recommendations:")
            lines.extend(f"- {rec}" for rec in self.recommendations)

        return "\n".join(lines) if len(lines) > 1 else "Diagnosis: inconclusive"


@dataclass
class MaintenanceTask:
    """
    维护任务。
    """

    id: str
    task_type: MaintenanceTaskType
    title: str
    description: str
    target_agent: str = "BackendAgent"
    priority: str = "medium"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        task_type: MaintenanceTaskType,
        title: str,
        description: str,
        target_agent: str = "BackendAgent",
        priority: str = "medium",
        metadata: dict[str, Any] | None = None,
    ) -> MaintenanceTask:

        return cls(
            id=f"maint_{uuid4().hex[:12]}",
            task_type=task_type,
            title=title,
            description=description,
            target_agent=target_agent,
            priority=priority,
            metadata=metadata or {},
        )


@dataclass
class MaintenanceResult:
    """
    维护任务执行结果。
    """

    success: bool
    tasks: list[MaintenanceTask] = field(default_factory=list)
    report_path: str = ""
    agent_results: list[dict[str, Any]] = field(default_factory=list)
    verification_passed: bool = False
    redeploy_success: bool = False
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationContext:
    """
    运维上下文，供 PromptBuilder 注入。
    """

    monitor_summary: str = ""
    alert_summary: str = ""
    incident_summary: str = ""
    diagnosis_summary: str = ""
    maintenance_summary: str = ""
    deployment_history_summary: str = ""

    def to_shared_context(self) -> dict[str, str]:

        return {
            "operation_monitor": self.monitor_summary,
            "operation_alerts": self.alert_summary,
            "operation_incident": self.incident_summary,
            "operation_diagnosis": self.diagnosis_summary,
            "operation_maintenance": self.maintenance_summary,
            "operation_deployment_history": self.deployment_history_summary,
        }

    def to_prompt_block(self) -> str:

        return (
            f"## Monitor\n{self.monitor_summary or 'n/a'}\n\n"
            f"## Alerts\n{self.alert_summary or 'none'}\n\n"
            f"## Incident\n{self.incident_summary or 'none'}\n\n"
            f"## Diagnosis\n{self.diagnosis_summary or 'n/a'}\n\n"
            f"## Maintenance\n{self.maintenance_summary or 'n/a'}\n\n"
            f"## Deployment History\n"
            f"{self.deployment_history_summary or 'n/a'}"
        )


@dataclass
class OperationPipelineResult:
    """
    完整运维流水线结果。
    """

    success: bool
    monitor: MonitorResult | None = None
    alerts: AlertResult | None = None
    incident: IncidentResult | None = None
    diagnosis: DiagnosisResult | None = None
    maintenance: MaintenanceResult | None = None
    context: OperationContext = field(default_factory=OperationContext)
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
