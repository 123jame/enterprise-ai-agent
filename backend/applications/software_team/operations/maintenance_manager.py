from __future__ import annotations

from pathlib import Path
from typing import Any

from app.agents.types import AgentContext
from app.agents.types import AgentResult
from app.memory.types import MemoryRecord

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.deployment.deployment_service import DeploymentService
from applications.software_team.execution.execution_manager import ExecutionManager
from applications.software_team.execution.verification_manager import VerificationManager
from applications.software_team.operations.operation_history import DiagnosisResult
from applications.software_team.operations.operation_history import MaintenanceResult
from applications.software_team.operations.operation_history import MaintenanceTask
from applications.software_team.operations.operation_history import MaintenanceTaskType
from applications.software_team.operations.operation_history import OperationContext
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.project import Project
from applications.software_team.project.workspace.workspace_manager import (
    WorkspaceManager,
)
from applications.software_team.runtime.team_agent_runtime import TeamAgentRuntime


class MaintenanceManager:
    """
    创建并执行维护任务（Bug Fix / Performance / Security Patch）。

    Auto Fix 可配置：经 Agent + Verification + Redeploy，不直接执行 shell。
    """

    REPORT_DIR = "operations"
    REPORT_NAME = "MAINTENANCE_REPORT.md"

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        execution_manager: ExecutionManager | None = None,
        verification_manager: VerificationManager | None = None,
        deployment_service: DeploymentService | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._execution = execution_manager or ExecutionManager(
            settings=self._settings,
        )
        self._verification = verification_manager or VerificationManager(
            settings=self._settings,
        )
        self._deployment = deployment_service or DeploymentService(
            settings=self._settings,
        )

    def create_tasks(
        self,
        diagnosis: DiagnosisResult,
    ) -> list[MaintenanceTask]:

        tasks: list[MaintenanceTask] = []

        for cause in diagnosis.root_causes:

            task_type = self._infer_task_type(cause)
            title = f"Fix: {cause[:60]}"
            description = (
                f"Root cause: {cause}\n\n"
                f"Recommendations:\n"
                + "\n".join(f"- {r}" for r in diagnosis.recommendations)
            )

            tasks.append(
                MaintenanceTask.create(
                    task_type=task_type,
                    title=title,
                    description=description,
                    target_agent=self._select_agent(task_type),
                    priority=(
                        "high"
                        if task_type == MaintenanceTaskType.SECURITY
                        else "medium"
                    ),
                    metadata={"root_cause": cause},
                )
            )

        if not tasks and diagnosis.recommendations:

            tasks.append(
                MaintenanceTask.create(
                    task_type=MaintenanceTaskType.GENERAL,
                    title="General maintenance",
                    description="\n".join(diagnosis.recommendations),
                )
            )

        return tasks

    def execute(
        self,
        project: Project,
        *,
        tasks: list[MaintenanceTask],
        operation_context: OperationContext,
        artifact_manager: ArtifactManager,
        workspace_manager: WorkspaceManager,
        team_runtime: TeamAgentRuntime | None = None,
        team_prompt_builder=None,
        session_id: str = "",
    ) -> MaintenanceResult:

        workspace_path = Path(project.workspace_path)
        agent_results: list[dict[str, Any]] = []
        verification_passed = True
        redeploy_success = False

        if (
            self._settings.operations_auto_fix
            and tasks
            and session_id
        ):

            from applications.software_team.agents.factory import TeamAgentFactory
            from applications.software_team.prompt.team_prompt_builder import (
                TeamPromptBuilder,
            )

            runtime = team_runtime or TeamAgentRuntime(
                settings=self._settings,
            )
            prompt_builder = team_prompt_builder or TeamPromptBuilder(
                config=runtime.config,
                memory_manager=runtime.memory_manager,
                tracer=runtime.tracer,
            )

            factory = TeamAgentFactory(
                project=project,
                artifact_manager=artifact_manager,
                workspace_manager=workspace_manager,
                team_agent_runtime=runtime,
                team_prompt_builder=prompt_builder,
            )

            for task in tasks[: self._settings.operations_max_fix_tasks]:

                agent_result = self._run_agent_fix(
                    factory=factory,
                    project=project,
                    task=task,
                    operation_context=operation_context,
                    session_id=session_id,
                    runtime=runtime,
                )

                agent_results.append({
                    "task_id": task.id,
                    "agent": task.target_agent,
                    "success": agent_result.success,
                    "content": (agent_result.content or "")[:500],
                })

                if not agent_result.success:

                    verification_passed = False
                    break

            if agent_results and all(r["success"] for r in agent_results):

                execution = self._execution.execute_target(
                    project.workspace_path,
                    "backend",
                )
                verification = self._verification.verify(
                    project.workspace_path,
                    target="backend",
                    execution_result=execution,
                )
                verification_passed = (
                    verification.success and execution.success
                )

            if verification_passed and self._settings.operations_auto_redeploy:

                deploy_result = self._deployment.run_pipeline(
                    project,
                    artifact_manager=artifact_manager,
                    memory_manager=runtime.memory_manager,
                    session_id=session_id,
                )
                redeploy_success = deploy_result.success

                if not deploy_result.success:

                    verification_passed = False

        report_path = self._write_report(
            workspace_path,
            tasks,
            agent_results,
            verification_passed,
            redeploy_success,
            diagnosis_summary=operation_context.diagnosis_summary,
        )

        success = (
            not self._settings.operations_auto_fix
            or (verification_passed and bool(agent_results or not tasks))
        )

        return MaintenanceResult(
            success=success,
            tasks=tasks,
            report_path=str(report_path),
            agent_results=agent_results,
            verification_passed=verification_passed,
            redeploy_success=redeploy_success,
            metadata={
                "auto_fix": self._settings.operations_auto_fix,
                "auto_redeploy": self._settings.operations_auto_redeploy,
            },
        )

    def _run_agent_fix(
        self,
        *,
        factory,
        project: Project,
        task: MaintenanceTask,
        operation_context: OperationContext,
        session_id: str,
        runtime: TeamAgentRuntime,
    ) -> AgentResult:

        from applications.software_team.agents.base.coordinator_context import (
            CoordinatorContext,
        )

        instruction = (
            f"## Maintenance Task: {task.title}\n\n"
            f"{task.description}\n\n"
            "Fix the production issue described above. "
            "Use write_file to update the codebase."
        )

        coordinator_context = CoordinatorContext(
            session_id=session_id,
            user_message=instruction,
            project=project,
            metadata={
                "current_task": instruction,
                "maintenance_task_id": task.id,
                "maintenance_task_type": task.task_type.value,
                "operations_mode": True,
            },
            shared_context={
                **operation_context.to_shared_context(),
                "workspace_path": project.workspace_path,
            },
        )

        agent_context = AgentContext(
            session_id=session_id,
            user_message=instruction,
            metadata=coordinator_context.metadata,
            agent_name=task.target_agent,
            agent_role="maintenance_engineer",
            shared_context=coordinator_context.shared_context,
        )

        runtime.memory_manager.memory.save(
            session_id,
            MemoryRecord(
                role="assistant",
                content=f"Maintenance task started: {task.title}",
                metadata={
                    "type": "memory",
                    "category": "maintenance_history",
                    "task_id": task.id,
                    "task_type": task.task_type.value,
                },
            ),
        )

        agent = factory.create(task.target_agent)

        return agent.run(agent_context)

    @staticmethod
    def _infer_task_type(cause: str) -> MaintenanceTaskType:

        lower = cause.lower()

        if "security" in lower or "patch" in lower:

            return MaintenanceTaskType.SECURITY

        if "performance" in lower or "cpu" in lower or "memory" in lower:

            return MaintenanceTaskType.PERFORMANCE

        if "exception" in lower or "import" in lower or "api" in lower:

            return MaintenanceTaskType.BUG_FIX

        return MaintenanceTaskType.GENERAL

    @staticmethod
    def _select_agent(task_type: MaintenanceTaskType) -> str:

        if task_type == MaintenanceTaskType.PERFORMANCE:

            return "BackendAgent"

        if task_type == MaintenanceTaskType.SECURITY:

            return "BackendAgent"

        return "BackendAgent"

    def _write_report(
        self,
        workspace: Path,
        tasks: list[MaintenanceTask],
        agent_results: list[dict[str, Any]],
        verification_passed: bool,
        redeploy_success: bool,
        *,
        diagnosis_summary: str,
    ) -> Path:

        report_dir = workspace / self.REPORT_DIR
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / self.REPORT_NAME

        task_lines = "\n".join(
            f"- [{t.task_type.value}] {t.title} → {t.target_agent}"
            for t in tasks
        ) or "- No tasks created"

        agent_lines = "\n".join(
            f"- {r['agent']}: {'OK' if r['success'] else 'FAIL'}"
            for r in agent_results
        ) or "- Auto fix not executed"

        content = f"""# Maintenance Report

## Tasks
{task_lines}

## Diagnosis
{diagnosis_summary or 'n/a'}

## Agent Fix Results
{agent_lines}

## Verification
{'PASS' if verification_passed else 'FAIL'}

## Redeploy
{'SUCCESS' if redeploy_success else 'SKIPPED/FAIL'}

---
*Generated by MaintenanceManager*
"""

        report_path.write_text(content, encoding=DEFAULT_ENCODING)

        return report_path
