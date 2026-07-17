"""
P10 Project Management 测试。

运行:
    cd backend
    python -m applications.software_team.tests.test_management
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.memory.manager import MemoryManager

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.management.management_result import ManagementContext
from applications.software_team.management.management_result import TaskStatus
from applications.software_team.management.management_service import ManagementService
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
from applications.software_team.project.models.project import Project
from applications.software_team.project.models.project_status import ProjectStatus


def _sample_project(root: Path) -> Project:

    return Project(
        id="proj-1",
        name="Library System",
        requirement="开发一个图书管理系统",
        description="Library management",
        workspace_path=str(root),
        status=ProjectStatus.CREATED,
        tech_stack=["python", "fastapi", "react"],
    )


def test_planning_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        project = _sample_project(root)

        result = PlanningManager().create_plan(project)

        assert result.success is True
        assert result.plan is not None
        assert len(result.plan.phases) == 6
        assert Path(result.plan_path).is_file()
        print("PlanningManager: PASS")


def test_task_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        project = _sample_project(root)

        planning = PlanningManager().create_plan(project)
        assert planning.plan is not None

        breakdown = TaskManager().breakdown(
            planning.plan,
            workspace=root,
        )

        assert breakdown.success is True
        assert len(breakdown.tasks) == 6
        assert breakdown.tasks[0].assignee == "ProductAgent"
        assert Path(breakdown.task_list_path).is_file()
        print("TaskManager: PASS")


def test_milestone_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        project = _sample_project(root)

        planning = PlanningManager().create_plan(project)
        breakdown = TaskManager().breakdown(
            planning.plan,
            workspace=root,
        )

        result = MilestoneManager().create_from_plan(
            planning.plan,
            breakdown.tasks,
            workspace=root,
        )

        assert result.success is True
        assert len(result.milestones) == 6
        assert result.current_milestone is not None
        assert Path(result.milestone_report_path).is_file()
        print("MilestoneManager: PASS")


def test_risk_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        project = _sample_project(root)

        planning = PlanningManager().create_plan(project)
        breakdown = TaskManager().breakdown(
            planning.plan,
            workspace=root,
        )
        milestones = MilestoneManager().create_from_plan(
            planning.plan,
            breakdown.tasks,
            workspace=root,
        )

        breakdown.tasks[2].status = TaskStatus.BLOCKED

        result = RiskManager().assess(
            project,
            tasks=breakdown.tasks,
            milestones=milestones.milestones,
            workspace=root,
            verification_failures=2,
            pipeline_failed=False,
        )

        assert result.success is True
        assert len(result.risks) >= 1
        assert Path(result.risk_report_path).is_file()
        print("RiskManager: PASS")


def test_progress_and_workload() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        project = _sample_project(root)

        planning = PlanningManager().create_plan(project)
        breakdown = TaskManager().breakdown(
            planning.plan,
            workspace=root,
        )

        breakdown.tasks[0].status = TaskStatus.COMPLETED
        breakdown.tasks[1].status = TaskStatus.IN_PROGRESS

        progress = ProgressManager().snapshot(
            project,
            breakdown.tasks,
            completed_agents=["ProductAgent"],
        )

        assert progress.completion_rate > 0
        assert progress.total_tasks == 6
        assert Path(progress.progress_report_path).is_file()

        workload = WorkloadManager().analyze(breakdown.tasks)

        assert "ArchitectAgent" in workload.loads
        assert isinstance(workload.balanced, bool)
        print("ProgressManager & WorkloadManager: PASS")


def test_project_manager() -> None:

    project = Project(
        id="p1",
        name="Demo",
        requirement="demo",
        workspace_path="/tmp/ws",
        status=ProjectStatus.CREATED,
    )

    manager = ProjectManager()
    state = manager.initialize(project)

    assert state.project_id == "p1"
    manager.mark_agent_completed(project, "ProductAgent")
    assert "ProductAgent" in state.completed_agents

    summary = manager.get_lifecycle_summary(project)
    assert "Demo" in summary
    print("ProjectManager: PASS")


def test_management_service_planning() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        project = _sample_project(root)

        settings = SoftwareTeamSettings(enable_project_management=True)
        service = ManagementService(settings=settings)
        memory = MemoryManager()
        artifacts = ArtifactManager()

        result = service.run_planning(
            project,
            artifact_manager=artifacts,
            memory_manager=memory,
            session_id="mgmt-plan",
        )

        assert result.success is True
        assert result.planning is not None
        assert result.tasks is not None
        assert len(result.tasks.tasks) == 6
        assert len(artifacts.find_management_artifacts()) >= 3

        memory_context = memory.load("mgmt-plan")
        categories = {
            r.metadata.get("category")
            for r in memory_context.records
        }
        assert "project_history" in categories
        assert "task_history" in categories
        assert "milestone_history" in categories
        print("ManagementService planning: PASS")


def test_management_service_lifecycle() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        project = _sample_project(root)

        settings = SoftwareTeamSettings(enable_project_management=True)
        service = ManagementService(settings=settings)
        memory = MemoryManager()
        artifacts = ArtifactManager()

        service.run_planning(
            project,
            artifact_manager=artifacts,
            memory_manager=memory,
            session_id="mgmt-life",
        )

        for agent in (
            "ProductAgent",
            "ArchitectAgent",
            "BackendAgent",
            "FrontendAgent",
            "QAAgent",
            "DocumentationAgent",
        ):

            service.on_agent_started(project, agent)
            service.on_agent_completed(
                project,
                agent,
                success=True,
                memory_manager=memory,
                session_id="mgmt-life",
            )

        final = service.finalize(
            project,
            artifact_manager=artifacts,
            memory_manager=memory,
            session_id="mgmt-life",
            pipeline_success=True,
        )

        assert final.success is True
        assert final.progress is not None
        assert final.progress.completion_rate == 1.0
        assert final.delivery is not None
        assert final.delivery.score >= 0.75
        assert len(artifacts.find_management_artifacts()) >= 5
        print("ManagementService lifecycle: PASS")


def test_team_prompt_builder_management_context() -> None:

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
        requirement="demo",
        workspace_path="/tmp/ws",
        status=ProjectStatus.PLANNING,
    )

    context = CoordinatorContext.from_agent_context(
        context=AgentContext(
            session_id="s1",
            user_message="build",
            metadata={"management_context": True},
        ),
        project=project,
    )

    mgmt_ctx = ManagementContext(
        project_summary="Project: Demo (planning)",
        current_milestone="Backend Development (in_progress)",
        current_sprint="Sprint-1-demo",
        task_status_summary="- BackendAgent: in_progress",
        risk_summary="Risks: none critical",
        progress_summary="Progress: 50% (3/6 tasks)",
    )

    builder = TeamPromptBuilder()
    messages = builder.build(
        "ProductAgent",
        context,
        ArtifactManager(),
        management_context=mgmt_ctx,
    )

    combined = "\n".join(m.content for m in messages)
    assert "Project Management Context" in combined
    assert "Backend Development" in combined
    print("TeamPromptBuilder management: PASS")


def main() -> None:

    test_planning_manager()
    test_task_manager()
    test_milestone_manager()
    test_risk_manager()
    test_progress_and_workload()
    test_project_manager()
    test_management_service_planning()
    test_management_service_lifecycle()
    test_team_prompt_builder_management_context()
    print("\nAll P10 management tests passed.")


if __name__ == "__main__":

    main()
