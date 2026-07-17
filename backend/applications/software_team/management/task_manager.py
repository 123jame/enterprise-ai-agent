from __future__ import annotations

from pathlib import Path

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.management.management_result import PlanPhase
from applications.software_team.management.management_result import ProjectPlan
from applications.software_team.management.management_result import TaskBreakdownResult
from applications.software_team.management.management_result import TaskItem
from applications.software_team.management.management_result import TaskPriority
from applications.software_team.management.management_result import TaskStatus
from applications.software_team.workflow.dependencies import AgentDependencyRegistry


class TaskManager:
    """
    自动拆分任务：优先级、负责人、状态、依赖关系。
    """

    REPORT_DIR = "management"
    TASK_LIST_NAME = "TASK_LIST.md"

    _PRIORITIES: dict[str, TaskPriority] = {
        "ProductAgent": TaskPriority.HIGH,
        "ArchitectAgent": TaskPriority.HIGH,
        "BackendAgent": TaskPriority.HIGH,
        "FrontendAgent": TaskPriority.MEDIUM,
        "QAAgent": TaskPriority.MEDIUM,
        "DocumentationAgent": TaskPriority.LOW,
    }

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        dependency_registry: AgentDependencyRegistry | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._registry = dependency_registry or AgentDependencyRegistry()

    def breakdown(
        self,
        plan: ProjectPlan,
        *,
        workspace: str | Path,
    ) -> TaskBreakdownResult:

        tasks: list[TaskItem] = []
        task_by_agent: dict[str, TaskItem] = {}

        for phase in plan.phases:

            dependencies = self._resolve_task_dependencies(
                phase.agent_name,
                task_by_agent,
            )

            task = TaskItem.create(
                title=phase.description or phase.name,
                assignee=phase.agent_name,
                priority=self._PRIORITIES.get(
                    phase.agent_name,
                    TaskPriority.MEDIUM,
                ),
                phase=phase.name,
                description=phase.description,
                dependencies=dependencies,
            )

            tasks.append(task)
            task_by_agent[phase.agent_name] = task

        task_list_path = self._write_task_list(workspace, plan, tasks)

        return TaskBreakdownResult(
            success=True,
            tasks=tasks,
            task_list_path=str(task_list_path),
        )

    def assign_next(
        self,
        tasks: list[TaskItem],
        agent_name: str,
    ) -> TaskItem | None:

        for task in tasks:

            if task.assignee == agent_name and task.status == TaskStatus.PENDING:

                task.status = TaskStatus.IN_PROGRESS

                return task

        return None

    def complete_task(
        self,
        tasks: list[TaskItem],
        agent_name: str,
        *,
        success: bool,
    ) -> TaskItem | None:

        for task in tasks:

            if task.assignee == agent_name and task.status in (
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS,
            ):

                task.status = (
                    TaskStatus.COMPLETED if success else TaskStatus.BLOCKED
                )

                return task

        return None

    def get_pending_tasks(
        self,
        tasks: list[TaskItem],
    ) -> list[TaskItem]:

        return [
            task
            for task in tasks
            if task.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
        ]

    def _resolve_task_dependencies(
        self,
        agent_name: str,
        task_by_agent: dict[str, TaskItem],
    ) -> list[str]:

        deps = self._registry.get_dependencies(agent_name)
        pipeline = [
            step.agent_name
            for step in self._registry.get_pipeline()
        ]

        if agent_name not in pipeline:

            return []

        index = pipeline.index(agent_name)
        dependency_ids: list[str] = []

        if not deps:

            return []

        if deps == ("*",):

            for prior_agent in pipeline[:index]:

                prior = task_by_agent.get(prior_agent)

                if prior is not None:

                    dependency_ids.append(prior.id)

            return dependency_ids

        output_to_agent: dict[str, str] = {}

        for prior_agent in pipeline[:index]:

            target = self._registry.get_verification_target(prior_agent)

            if target:

                output_to_agent[target] = prior_agent
                output_to_agent[target.split("/")[-1]] = prior_agent

        for dep in deps:

            producer = output_to_agent.get(dep)

            if producer is None:

                for key, agent in output_to_agent.items():

                    if dep in key or key in dep:

                        producer = agent
                        break

            if producer is not None:

                prior = task_by_agent.get(producer)

                if prior is not None:

                    dependency_ids.append(prior.id)

        return list(dict.fromkeys(dependency_ids))

    def _write_task_list(
        self,
        workspace: str | Path,
        plan: ProjectPlan,
        tasks: list[TaskItem],
    ) -> Path:

        workspace_path = Path(workspace)
        report_dir = workspace_path / self.REPORT_DIR
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / self.TASK_LIST_NAME

        lines = "\n".join(
            f"| {task.id} | {task.title} | {task.assignee} | "
            f"{task.priority.value} | {task.status.value} | "
            f"{', '.join(task.dependencies) or '-'} |"
            for task in tasks
        )

        content = f"""# Task List — {plan.project_name}

| ID | Task | Assignee | Priority | Status | Dependencies |
|----|------|----------|----------|--------|--------------|
{lines}

---
*Generated by TaskManager*
"""

        report_path.write_text(content, encoding=DEFAULT_ENCODING)

        return report_path
