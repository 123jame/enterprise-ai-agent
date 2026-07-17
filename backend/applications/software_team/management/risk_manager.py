from __future__ import annotations

from pathlib import Path

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.management.management_result import Milestone
from applications.software_team.management.management_result import MilestoneStatus
from applications.software_team.management.management_result import Risk
from applications.software_team.management.management_result import RiskAssessmentResult
from applications.software_team.management.management_result import RiskLevel
from applications.software_team.management.management_result import RiskStatus
from applications.software_team.management.management_result import TaskItem
from applications.software_team.management.management_result import TaskStatus
from applications.software_team.project.models.project import Project


class RiskManager:
    """
    识别和记录项目风险：开发延期、需求变更、测试失败等。
    """

    REPORT_DIR = "management"
    REPORT_NAME = "RISK_REPORT.md"

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()

    def assess(
        self,
        project: Project,
        *,
        tasks: list[TaskItem],
        milestones: list[Milestone],
        workspace: str | Path,
        verification_failures: int = 0,
        pipeline_failed: bool = False,
    ) -> RiskAssessmentResult:

        risks: list[Risk] = []

        blocked = [
            task for task in tasks if task.status == TaskStatus.BLOCKED
        ]

        if blocked:

            risks.append(
                Risk.create(
                    title="Task blocked after agent failure",
                    level=RiskLevel.HIGH,
                    category="development_delay",
                    description=(
                        f"{len(blocked)} task(s) blocked: "
                        + ", ".join(t.assignee for t in blocked)
                    ),
                    mitigation="Review failed agent output and retry verification",
                )
            )

        delayed = [
            m for m in milestones if m.status == MilestoneStatus.DELAYED
        ]

        if delayed:

            risks.append(
                Risk.create(
                    title="Milestone delay",
                    level=RiskLevel.MEDIUM,
                    category="development_delay",
                    description=(
                        f"Delayed milestones: "
                        + ", ".join(m.name for m in delayed)
                    ),
                    mitigation="Re-plan timeline or reduce scope",
                )
            )

        if verification_failures > 0:

            risks.append(
                Risk.create(
                    title="Verification failures detected",
                    level=RiskLevel.HIGH,
                    category="test_failure",
                    description=(
                        f"{verification_failures} verification retry(s) occurred"
                    ),
                    mitigation="Fix code quality issues before delivery",
                )
            )

        if pipeline_failed:

            risks.append(
                Risk.create(
                    title="Pipeline execution failed",
                    level=RiskLevel.CRITICAL,
                    category="development_delay",
                    description="Software team pipeline did not complete successfully",
                    mitigation="Investigate failed agent step and restart pipeline",
                )
            )

        pending_high = [
            task
            for task in tasks
            if task.status == TaskStatus.PENDING
            and task.priority.value == "high"
        ]

        if len(pending_high) > 2:

            risks.append(
                Risk.create(
                    title="High-priority backlog",
                    level=RiskLevel.MEDIUM,
                    category="resource_constraint",
                    description=(
                        f"{len(pending_high)} high-priority tasks still pending"
                    ),
                    mitigation="Prioritize critical path tasks",
                )
            )

        if not risks:

            risks.append(
                Risk.create(
                    title="No critical risks identified",
                    level=RiskLevel.LOW,
                    category="monitoring",
                    description="Current project status within acceptable bounds",
                    status=RiskStatus.CLOSED,
                )
            )

        report_path = self._write_report(workspace, project, risks)
        summary = self._build_summary(risks)

        return RiskAssessmentResult(
            success=True,
            risks=risks,
            risk_report_path=str(report_path),
            summary=summary,
        )

    def _build_summary(self, risks: list[Risk]) -> str:

        open_risks = [
            r for r in risks if r.status == RiskStatus.OPEN
        ]

        if not open_risks:

            return "Risks: none critical"

        lines = [f"Risks: {len(open_risks)} open"]

        for risk in open_risks:

            lines.append(
                f"- [{risk.level.value}] {risk.title}: {risk.description[:80]}"
            )

        return "\n".join(lines)

    def _write_report(
        self,
        workspace: str | Path,
        project: Project,
        risks: list[Risk],
    ) -> Path:

        workspace_path = Path(workspace)
        report_dir = workspace_path / self.REPORT_DIR
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / self.REPORT_NAME

        lines = "\n".join(
            f"| {r.title} | {r.level.value} | {r.status.value} | "
            f"{r.category} | {r.mitigation[:60]} |"
            for r in risks
        )

        content = f"""# Risk Report — {project.name}

| Risk | Level | Status | Category | Mitigation |
|------|-------|--------|----------|------------|
{lines}

---
*Generated by RiskManager*
"""

        report_path.write_text(content, encoding=DEFAULT_ENCODING)

        return report_path
