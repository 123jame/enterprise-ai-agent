from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.memory.manager import MemoryManager
from app.memory.types import MemoryRecord

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.management.management_result import DeliveryEvaluation
from applications.software_team.management.management_result import ManagementContext
from applications.software_team.management.management_result import ManagementEventType
from applications.software_team.management.management_result import ManagementPipelineResult
from applications.software_team.management.management_result import Milestone
from applications.software_team.management.management_result import MilestoneResult
from applications.software_team.management.management_result import PlanningResult
from applications.software_team.management.management_result import ProgressSnapshot
from applications.software_team.management.management_result import RiskAssessmentResult
from applications.software_team.management.management_result import TaskBreakdownResult
from applications.software_team.management.management_result import WorkloadSnapshot
from applications.software_team.management.milestone_manager import MilestoneManager
from applications.software_team.management.planning_manager import PlanningManager
from applications.software_team.management.progress_manager import ProgressManager
from applications.software_team.management.project_manager import ProjectManager
from applications.software_team.management.risk_manager import RiskManager
from applications.software_team.management.task_manager import TaskManager
from applications.software_team.management.workload_manager import WorkloadManager
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.artifact import Artifact
from applications.software_team.project.models.project import Project
from applications.software_team.project.services.project_service import (
    ProjectService,
)


class ManagementService:
    """
    项目管理流水线编排：

    Planning → Task Assignment → (Agent Execution hooks)
    → Progress Update → Milestone Check → Risk Assessment → Delivery Evaluation
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        project_manager: ProjectManager | None = None,
        planning_manager: PlanningManager | None = None,
        task_manager: TaskManager | None = None,
        milestone_manager: MilestoneManager | None = None,
        risk_manager: RiskManager | None = None,
        progress_manager: ProgressManager | None = None,
        workload_manager: WorkloadManager | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._project = project_manager or ProjectManager(
            settings=self._settings,
        )
        self._planning = planning_manager or PlanningManager(
            settings=self._settings,
        )
        self._tasks = task_manager or TaskManager(
            settings=self._settings,
        )
        self._milestones = milestone_manager or MilestoneManager(
            settings=self._settings,
        )
        self._risks = risk_manager or RiskManager(
            settings=self._settings,
        )
        self._progress = progress_manager or ProgressManager(
            settings=self._settings,
        )
        self._workload = workload_manager or WorkloadManager(
            settings=self._settings,
        )
        self._verification_failures = 0

    @property
    def enabled(self) -> bool:

        return self._settings.enable_project_management

    def bind_project_service(
        self,
        project_service: ProjectService,
    ) -> None:

        self._project._project_service = project_service

    def run_planning(
        self,
        project: Project,
        *,
        artifact_manager: ArtifactManager,
        memory_manager: MemoryManager | None = None,
        session_id: str = "",
    ) -> ManagementPipelineResult:
        """
        项目启动：Planning → Task Breakdown → Milestone 创建。
        """

        if not self.enabled:

            return ManagementPipelineResult(
                success=True,
                metadata={"skipped": True},
            )

        state = self._project.initialize(project)

        planning = self._planning.create_plan(project)

        if not planning.success or planning.plan is None:

            return ManagementPipelineResult(
                success=False,
                planning=planning,
                error_message=planning.error_message or "Planning failed",
            )

        state.plan = planning.plan

        self._save_memory(
            memory_manager,
            session_id,
            ManagementEventType.PROJECT,
            f"Plan created: {planning.plan.total_duration_days} days",
            {"phases": len(planning.plan.phases)},
        )

        breakdown = self._tasks.breakdown(
            planning.plan,
            workspace=project.workspace_path,
        )

        state.tasks = breakdown.tasks

        for task in breakdown.tasks:

            project.add_task(task.id)

        self._save_memory(
            memory_manager,
            session_id,
            ManagementEventType.TASK,
            f"Tasks created: {len(breakdown.tasks)}",
            {"count": len(breakdown.tasks)},
        )

        milestone_result = self._milestones.create_from_plan(
            planning.plan,
            breakdown.tasks,
            workspace=project.workspace_path,
        )

        state.milestones = milestone_result.milestones

        self._save_memory(
            memory_manager,
            session_id,
            ManagementEventType.MILESTONE,
            f"Milestones: {len(milestone_result.milestones)}",
            {},
        )

        self._register_planning_artifacts(
            artifact_manager,
            planning,
            breakdown,
            milestone_result,
        )

        context = self.build_context(project)

        return ManagementPipelineResult(
            success=True,
            planning=planning,
            tasks=breakdown,
            milestones=milestone_result,
            context=context,
            metadata={"phase": "planning"},
        )

    def on_agent_started(
        self,
        project: Project,
        agent_name: str,
    ) -> None:

        if not self.enabled:

            return

        state = self._project.ensure_state(project)

        self._tasks.assign_next(state.tasks, agent_name)

    def on_agent_completed(
        self,
        project: Project,
        agent_name: str,
        *,
        success: bool,
        memory_manager: MemoryManager | None = None,
        session_id: str = "",
    ) -> ManagementContext:
        """
        Agent 完成后更新任务、里程碑、进度。
        """

        if not self.enabled:

            return ManagementContext()

        state = self._project.ensure_state(project)

        completed_task = self._tasks.complete_task(
            state.tasks,
            agent_name,
            success=success,
        )

        if success:

            self._project.mark_agent_completed(project, agent_name)

        current = self._milestones.on_task_completed(
            state.milestones,
            state.tasks,
            agent_name=agent_name,
        )

        if current is not None:

            milestone_result = MilestoneResult(
                success=True,
                milestones=state.milestones,
                current_milestone=current,
            )

            self._save_memory(
                memory_manager,
                session_id,
                ManagementEventType.MILESTONE,
                f"Milestone update: {current.name} ({current.status.value})",
                {"milestone_id": current.id},
            )

        if completed_task is not None:

            self._save_memory(
                memory_manager,
                session_id,
                ManagementEventType.TASK,
                f"Task {completed_task.id} → {completed_task.status.value}",
                {"agent": agent_name},
            )

        return self.build_context(project)

    def record_verification_failure(self) -> None:

        self._verification_failures += 1

    def finalize(
        self,
        project: Project,
        *,
        artifact_manager: ArtifactManager,
        memory_manager: MemoryManager | None = None,
        session_id: str = "",
        pipeline_success: bool = True,
        completed_steps: list[str] | None = None,
    ) -> ManagementPipelineResult:
        """
        项目收尾：Progress → Milestone Check → Risk → Delivery Evaluation。
        """

        if not self.enabled:

            return ManagementPipelineResult(
                success=True,
                metadata={"skipped": True},
            )

        state = self._project.ensure_state(project)

        steps = completed_steps if completed_steps else state.completed_agents

        delayed = self._milestones.check_delays(state.milestones)

        progress = self._progress.snapshot(
            project,
            state.tasks,
            completed_agents=state.completed_agents,
        )

        self._save_memory(
            memory_manager,
            session_id,
            ManagementEventType.PROGRESS,
            progress.summary,
            {"rate": progress.completion_rate},
        )

        workload = self._workload.analyze(state.tasks)

        risks = self._risks.assess(
            project,
            tasks=state.tasks,
            milestones=state.milestones,
            workspace=project.workspace_path,
            verification_failures=self._verification_failures,
            pipeline_failed=not pipeline_success,
        )

        state.risks = risks.risks

        self._save_memory(
            memory_manager,
            session_id,
            ManagementEventType.RISK,
            risks.summary,
            {"count": len(risks.risks)},
        )

        delivery = self._evaluate_delivery(
            project,
            progress,
            risks,
            pipeline_success=pipeline_success,
            completed_steps=steps,
        )

        self._save_memory(
            memory_manager,
            session_id,
            ManagementEventType.DELIVERY,
            delivery.summary,
            {"score": delivery.score},
        )

        self._project.mark_complete(project, success=pipeline_success)

        self._register_finalize_artifacts(
            artifact_manager,
            progress,
            risks,
        )

        context = self.build_context(
            project,
            progress=progress,
            workload=workload,
            risks=risks,
        )

        return ManagementPipelineResult(
            success=pipeline_success and delivery.success,
            milestones=MilestoneResult(
                success=True,
                milestones=state.milestones,
                current_milestone=self._current_milestone(state),
            ),
            risks=risks,
            progress=progress,
            workload=workload,
            delivery=delivery,
            context=context,
            metadata={
                "delayed_milestones": len(delayed),
                "delivery_score": delivery.score,
            },
        )

    def build_context(
        self,
        project: Project,
        *,
        progress: ProgressSnapshot | None = None,
        workload: WorkloadSnapshot | None = None,
        risks: RiskAssessmentResult | None = None,
    ) -> ManagementContext:

        state = self._project.get_state(project.id)

        if state is None:

            return ManagementContext(
                project_summary=f"Project: {project.name}",
            )

        if progress is None:

            progress = self._progress.snapshot(
                project,
                state.tasks,
                completed_agents=state.completed_agents,
            )

        if workload is None:

            workload = self._workload.analyze(state.tasks)

        if risks is None and state.risks:

            open_risks = [
                r for r in state.risks if r.status.value == "open"
            ]
            risk_summary = (
                f"Risks: {len(open_risks)} open"
                if open_risks
                else "Risks: none critical"
            )
            risks = RiskAssessmentResult(
                success=True,
                risks=state.risks,
                summary=risk_summary,
            )

        current_milestone = self._current_milestone(state)

        task_lines = "\n".join(
            f"- {t.assignee}: {t.status.value}"
            for t in state.tasks
        )

        return ManagementContext(
            project_summary=self._project.get_lifecycle_summary(project),
            current_milestone=(
                f"{current_milestone.name} ({current_milestone.status.value})"
                if current_milestone
                else "n/a"
            ),
            current_sprint=state.current_sprint,
            task_status_summary=task_lines,
            risk_summary=risks.summary if risks else "none",
            progress_summary=progress.summary,
            workload_summary=workload.summary,
        )

    @staticmethod
    def _current_milestone(state) -> Milestone | None:

        for milestone in state.milestones:

            if milestone.status.value in ("in_progress", "delayed"):

                return milestone

        for milestone in reversed(state.milestones):

            if milestone.status.value == "completed":

                return milestone

        return state.milestones[0] if state.milestones else None

    def _evaluate_delivery(
        self,
        project: Project,
        progress: ProgressSnapshot,
        risks: RiskAssessmentResult,
        *,
        pipeline_success: bool,
        completed_steps: list[str],
    ) -> DeliveryEvaluation:

        open_critical = any(
            r.level.value in ("high", "critical")
            and r.status.value == "open"
            for r in risks.risks
        )

        criteria = {
            "pipeline_success": pipeline_success,
            "tasks_complete": progress.completion_rate >= 1.0,
            "no_critical_risks": not open_critical,
            "agents_executed": len(completed_steps) >= 6,
        }

        passed = sum(1 for ok in criteria.values() if ok)
        score = passed / len(criteria) if criteria else 0.0

        summary = (
            f"Delivery score: {score:.0%} — "
            + ", ".join(
                f"{k}={'PASS' if v else 'FAIL'}"
                for k, v in criteria.items()
            )
        )

        return DeliveryEvaluation(
            success=score >= 0.75 and pipeline_success,
            score=score,
            criteria=criteria,
            summary=summary,
        )

    @staticmethod
    def _register_planning_artifacts(
        artifact_manager: ArtifactManager,
        planning: PlanningResult,
        breakdown: TaskBreakdownResult,
        milestones: MilestoneResult,
    ) -> None:

        mappings = [
            (planning.plan_path, "PROJECT_PLAN.md", "project_plan"),
            (breakdown.task_list_path, "TASK_LIST.md", "task_list"),
            (
                milestones.milestone_report_path,
                "MILESTONE_REPORT.md",
                "milestone_report",
            ),
        ]

        for path, name, artifact_type in mappings:

            if not path:

                continue

            artifact_manager.register_management_artifact(
                Artifact(
                    id=f"artifact_{uuid4().hex[:12]}",
                    name=name,
                    type=artifact_type,
                    path=path,
                    owner="ManagementService",
                    metadata={"stage": "planning"},
                )
            )

    @staticmethod
    def _register_finalize_artifacts(
        artifact_manager: ArtifactManager,
        progress: ProgressSnapshot,
        risks: RiskAssessmentResult,
    ) -> None:

        mappings = [
            (progress.progress_report_path, "PROGRESS_REPORT.md", "progress_report"),
            (risks.risk_report_path, "RISK_REPORT.md", "risk_report"),
        ]

        for path, name, artifact_type in mappings:

            if not path:

                continue

            artifact_manager.register_management_artifact(
                Artifact(
                    id=f"artifact_{uuid4().hex[:12]}",
                    name=name,
                    type=artifact_type,
                    path=path,
                    owner="ManagementService",
                    metadata={"stage": "delivery"},
                )
            )

    @staticmethod
    def _save_memory(
        memory_manager: MemoryManager | None,
        session_id: str,
        event_type: ManagementEventType,
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
