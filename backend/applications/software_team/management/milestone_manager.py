from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from pathlib import Path

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.management.management_result import Milestone
from applications.software_team.management.management_result import MilestoneResult
from applications.software_team.management.management_result import MilestoneStatus
from applications.software_team.management.management_result import PlanPhase
from applications.software_team.management.management_result import ProjectPlan
from applications.software_team.management.management_result import TaskItem
from applications.software_team.management.management_result import TaskStatus


class MilestoneManager:
    """
    管理项目里程碑：创建、完成、延期。
    """

    REPORT_DIR = "management"
    REPORT_NAME = "MILESTONE_REPORT.md"

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()

    def create_from_plan(
        self,
        plan: ProjectPlan,
        tasks: list[TaskItem],
        *,
        workspace: str | Path,
    ) -> MilestoneResult:

        milestones: list[Milestone] = []
        start = datetime.utcnow()

        task_by_phase: dict[str, list[str]] = {}

        for task in tasks:

            task_by_phase.setdefault(task.phase, []).append(task.id)

        offset_days = 0

        for phase in plan.phases:

            target = start + timedelta(
                days=offset_days + phase.duration_days,
            )

            milestone = Milestone.create(
                name=phase.name,
                phase=phase.name,
                description=phase.description,
                target_date=target.strftime("%Y-%m-%d"),
                task_ids=task_by_phase.get(phase.name, []),
            )

            milestones.append(milestone)
            offset_days += phase.duration_days

        if milestones:

            milestones[0].status = MilestoneStatus.IN_PROGRESS

        report_path = self._write_report(workspace, plan, milestones)

        return MilestoneResult(
            success=True,
            milestones=milestones,
            milestone_report_path=str(report_path),
            current_milestone=milestones[0] if milestones else None,
        )

    def on_task_completed(
        self,
        milestones: list[Milestone],
        tasks: list[TaskItem],
        *,
        agent_name: str,
    ) -> Milestone | None:

        task_map = {task.id: task for task in tasks}

        for milestone in milestones:

            if milestone.status == MilestoneStatus.COMPLETED:

                continue

            related = [
                task_map[task_id]
                for task_id in milestone.task_ids
                if task_id in task_map
            ]

            if not related:

                continue

            if all(t.status == TaskStatus.COMPLETED for t in related):

                milestone.status = MilestoneStatus.COMPLETED

                next_milestone = self._activate_next(milestones, milestone)

                return next_milestone or milestone

            if any(t.assignee == agent_name for t in related):

                if milestone.status == MilestoneStatus.PENDING:

                    milestone.status = MilestoneStatus.IN_PROGRESS

                return milestone

        return None

    def check_delays(
        self,
        milestones: list[Milestone],
    ) -> list[Milestone]:

        today = datetime.utcnow().strftime("%Y-%m-%d")
        delayed: list[Milestone] = []

        for milestone in milestones:

            if (
                milestone.status not in (
                    MilestoneStatus.COMPLETED,
                    MilestoneStatus.DELAYED,
                )
                and milestone.target_date
                and milestone.target_date < today
            ):

                milestone.status = MilestoneStatus.DELAYED
                delayed.append(milestone)

        return delayed

    @staticmethod
    def _activate_next(
        milestones: list[Milestone],
        completed: Milestone,
    ) -> Milestone | None:

        found = False

        for milestone in milestones:

            if milestone.id == completed.id:

                found = True
                continue

            if found and milestone.status == MilestoneStatus.PENDING:

                milestone.status = MilestoneStatus.IN_PROGRESS

                return milestone

        return None

    def _write_report(
        self,
        workspace: str | Path,
        plan: ProjectPlan,
        milestones: list[Milestone],
    ) -> Path:

        workspace_path = Path(workspace)
        report_dir = workspace_path / self.REPORT_DIR
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / self.REPORT_NAME

        lines = "\n".join(
            f"| {m.name} | {m.status.value} | {m.target_date} | "
            f"{len(m.task_ids)} |"
            for m in milestones
        )

        content = f"""# Milestone Report — {plan.project_name}

| Milestone | Status | Target Date | Tasks |
|-----------|--------|-------------|-------|
{lines}

---
*Generated by MilestoneManager*
"""

        report_path.write_text(content, encoding=DEFAULT_ENCODING)

        return report_path
