from __future__ import annotations

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.operations.operation_history import Alert
from applications.software_team.operations.operation_history import AlertResult
from applications.software_team.operations.operation_history import AlertSeverity
from applications.software_team.operations.operation_history import MonitorResult


class AlertManager:
    """
    异常告警评估。

    支持错误率、响应时间、服务不可用、健康检查失败。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()

    def evaluate(
        self,
        monitor: MonitorResult,
    ) -> AlertResult:

        alerts: list[Alert] = []

        for metric in monitor.metrics:

            alert = self._evaluate_metric(metric)

            if alert is not None:

                alerts.append(alert)

        if not monitor.success and not alerts:

            alerts.append(
                Alert.create(
                    alert_type="monitor_failure",
                    severity=AlertSeverity.CRITICAL,
                    message=monitor.error_message or "Monitor collection failed",
                )
            )

        return AlertResult(
            success=True,
            has_alerts=len(alerts) > 0,
            alerts=alerts,
            metadata={"alert_count": len(alerts)},
        )

    def _evaluate_metric(
        self,
        metric,
    ) -> Alert | None:

        if metric.metadata.get("skipped"):

            return None

        if metric.name == "api_status" and not metric.success:

            return Alert.create(
                alert_type="service_unavailable",
                severity=AlertSeverity.CRITICAL,
                message=metric.message or "API is unreachable",
                metric_name=metric.name,
                actual_value=metric.value,
            )

        if metric.name == "api_status" and metric.success:

            if metric.value > self._settings.operations_alert_response_time_ms:

                return Alert.create(
                    alert_type="response_time",
                    severity=AlertSeverity.WARNING,
                    message=(
                        f"Response time {metric.value:.0f}ms exceeds "
                        f"{self._settings.operations_alert_response_time_ms}ms"
                    ),
                    metric_name=metric.name,
                    threshold=float(
                        self._settings.operations_alert_response_time_ms
                    ),
                    actual_value=metric.value,
                )

        if metric.name == "health_check" and not metric.success:

            return Alert.create(
                alert_type="health_check_failed",
                severity=AlertSeverity.CRITICAL,
                message=metric.message or "Health check failed",
                metric_name=metric.name,
                actual_value=metric.value,
            )

        if metric.name in ("cpu", "memory", "disk") and not metric.success:

            threshold_map = {
                "cpu": self._settings.operations_cpu_threshold_percent,
                "memory": self._settings.operations_memory_threshold_percent,
                "disk": self._settings.operations_disk_threshold_percent,
            }

            return Alert.create(
                alert_type=f"{metric.name}_threshold",
                severity=AlertSeverity.WARNING,
                message=metric.message,
                metric_name=metric.name,
                threshold=threshold_map.get(metric.name, 0.0),
                actual_value=metric.value,
            )

        if metric.name == "service_status" and not metric.success:

            return Alert.create(
                alert_type="service_degraded",
                severity=AlertSeverity.WARNING,
                message=metric.message or "Service deployment incomplete",
                metric_name=metric.name,
                actual_value=metric.value,
            )

        if metric.name == "database" and not metric.success:

            return Alert.create(
                alert_type="database_error",
                severity=AlertSeverity.CRITICAL,
                message=metric.message or "Database check failed",
                metric_name=metric.name,
                actual_value=metric.value,
            )

        return None

    def compute_error_rate(
        self,
        monitor: MonitorResult,
    ) -> float:

        if not monitor.metrics:

            return 0.0

        failed = sum(1 for m in monitor.metrics if not m.success)

        return failed / len(monitor.metrics)

    def evaluate_error_rate(
        self,
        monitor: MonitorResult,
    ) -> Alert | None:

        rate = self.compute_error_rate(monitor)
        threshold = self._settings.operations_alert_error_rate

        if rate <= threshold:

            return None

        return Alert.create(
            alert_type="error_rate",
            severity=AlertSeverity.CRITICAL,
            message=(
                f"Error rate {rate:.1%} exceeds threshold {threshold:.1%}"
            ),
            metric_name="error_rate",
            threshold=threshold,
            actual_value=rate,
        )
