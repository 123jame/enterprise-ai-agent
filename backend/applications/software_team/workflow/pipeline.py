from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Callable

from app.agents.types import AgentContext
from app.agents.types import AgentResult
from app.memory.types import MemoryRecord

from applications.software_team.agents.base.coordinator_context import (
    CoordinatorContext,
)
from applications.software_team.agents.factory import TeamAgentFactory
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.execution.execution_manager import ExecutionManager
from applications.software_team.execution.execution_result import ExecutionResult
from applications.software_team.execution.retry_policy import RetryPolicy
from applications.software_team.execution.verification_manager import (
    VerificationManager,
)
from applications.software_team.git.git_context import GitContext
from applications.software_team.git.git_context import GitEventType
from applications.software_team.git.git_service import GitService
from applications.software_team.deployment.deployment_service import DeploymentService
from applications.software_team.operations.operations_service import OperationsService
from applications.software_team.management.management_service import ManagementService
from applications.software_team.knowledge.knowledge_service import KnowledgeService
from applications.software_team.project.models.project import Project
from applications.software_team.project.models.project_status import ProjectStatus
from applications.software_team.project.services.project_service import (
    ProjectService,
)
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.workspace.workspace_manager import (
    WorkspaceManager,
)
from applications.software_team.prompt.team_prompt_builder import TeamPromptBuilder
from applications.software_team.runtime.team_agent_runtime import TeamAgentRuntime
from applications.software_team.workflow.artifact_reader import (
    ArtifactDependencyError,
)
from applications.software_team.workflow.dependencies import AgentDependencyRegistry
from applications.software_team.workflow.dependencies import PipelineStep


class PipelineExecutionError(Exception):
    """
    流水线执行失败。
    """

    def __init__(
        self,
        agent_name: str,
        message: str,
        step_index: int = 0,
    ):

        super().__init__(message)
        self.agent_name = agent_name
        self.step_index = step_index


@dataclass
class PipelineResult:
    """
    流水线执行结果摘要。
    """

    success: bool

    completed_steps: list[str] = field(
        default_factory=list,
    )

    failed_agent: str = ""

    error_message: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


class SoftwareTeamPipeline:
    """
    Software Team 顺序流水线（P6：含执行与验证重试；P7：含 Git 协作）。

    Generate → Execute → Verify → Git Commit → Next Agent
    由 Pipeline 编排，Agent 不直接运行命令或 Git。
    """

    def __init__(
        self,
        project_service: ProjectService,
        artifact_manager: ArtifactManager,
        workspace_manager: WorkspaceManager,
        settings: SoftwareTeamSettings | None = None,
        dependency_registry: AgentDependencyRegistry | None = None,
        team_agent_runtime: TeamAgentRuntime | None = None,
        team_prompt_builder: TeamPromptBuilder | None = None,
        execution_manager: ExecutionManager | None = None,
        verification_manager: VerificationManager | None = None,
        retry_policy: RetryPolicy | None = None,
        git_service: GitService | None = None,
        deployment_service: DeploymentService | None = None,
        operations_service: OperationsService | None = None,
        management_service: ManagementService | None = None,
        knowledge_service: KnowledgeService | None = None,
        on_status_change: Callable[[ProjectStatus], None] | None = None,
        on_agent_started: Callable[[str, str], None] | None = None,
        on_agent_finished: Callable[[str, bool, dict[str, Any]], None] | None = None,
        on_git_event: Callable[[dict[str, Any]], None] | None = None,
        on_deployment_finished: Callable[[dict[str, Any]], None] | None = None,
        on_operation_update: Callable[[dict[str, Any]], None] | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._project_service = project_service
        self._artifact_manager = artifact_manager
        self._workspace_manager = workspace_manager
        self._registry = (
            dependency_registry or AgentDependencyRegistry()
        )
        self._runtime = team_agent_runtime
        self._team_prompt_builder = team_prompt_builder
        self._execution_manager = (
            execution_manager
            or ExecutionManager(settings=self._settings)
        )
        self._verification_manager = (
            verification_manager
            or VerificationManager(settings=self._settings)
        )
        self._retry_policy = (
            retry_policy or RetryPolicy(settings=self._settings)
        )
        self._git_service = git_service or GitService(
            settings=self._settings,
        )
        self._deployment_service = (
            deployment_service
            or DeploymentService(settings=self._settings)
        )
        self._operations_service = (
            operations_service
            or OperationsService(settings=self._settings)
        )
        self._management_service = (
            management_service
            or ManagementService(settings=self._settings)
        )
        self._knowledge_service = (
            knowledge_service
            or KnowledgeService(settings=self._settings)
        )
        self._on_status_change = on_status_change
        self._on_agent_started = on_agent_started
        self._on_agent_finished = on_agent_finished
        self._on_git_event = on_git_event
        self._on_deployment_finished = on_deployment_finished
        self._on_operation_update = on_operation_update

    def run(
        self,
        context: AgentContext,
        project: Project,
    ) -> AgentResult:

        pipeline_result = self.execute(context, project)

        if pipeline_result.success:

            return AgentResult(
                success=True,
                model="pipeline",
                content=self._build_success_summary(
                    project,
                    pipeline_result,
                ),
            )

        return AgentResult(
            success=False,
            model="pipeline",
            content=(
                f"Pipeline 在 {pipeline_result.failed_agent} 失败: "
                f"{pipeline_result.error_message}"
            ),
        )

    def execute(
        self,
        context: AgentContext,
        project: Project,
    ) -> PipelineResult:

        team_context = CoordinatorContext.from_agent_context(
            context=context,
            project=project,
        )

        runtime = self._runtime or TeamAgentRuntime(
            settings=self._settings,
        )

        team_prompt_builder = (
            self._team_prompt_builder
            or TeamPromptBuilder(
                dependency_registry=self._registry,
                config=runtime.config,
                memory_manager=runtime.memory_manager,
                tracer=runtime.tracer,
            )
        )

        factory = TeamAgentFactory(
            project=project,
            artifact_manager=self._artifact_manager,
            workspace_manager=self._workspace_manager,
            team_agent_runtime=runtime,
            team_prompt_builder=team_prompt_builder,
        )

        completed: list[str] = []
        verification_log: list[dict[str, Any]] = []
        git_log: list[dict[str, Any]] = []

        init_git = self._git_service.initialize_project(project)

        if init_git.success and self._git_service.enabled:

            GitService.save_git_memory(
                memory_manager=runtime.memory_manager,
                session_id=context.session_id,
                event_type=GitEventType.INIT,
                content=f"Git initialized for {project.name}",
                metadata={"workspace": project.workspace_path},
            )

        git_context = self._git_service.build_context(project)

        if self._knowledge_service.enabled:

            self._knowledge_service.initialize(
                project,
                artifact_manager=self._artifact_manager,
                memory_manager=runtime.memory_manager,
                session_id=context.session_id,
            )

        for index, step in enumerate(
            self._registry.get_pipeline()
        ):

            self._update_status(step.status)

            try:

                agent = factory.create(step.agent_name)

                if self._on_agent_started is not None:

                    self._on_agent_started(step.agent_name, step.task)

                if self._management_service.enabled:

                    self._management_service.on_agent_started(
                        project,
                        step.agent_name,
                    )

                knowledge_context = None

                if self._knowledge_service.enabled:

                    knowledge_result = (
                        self._knowledge_service.prepare_for_agent(
                            project,
                            agent_name=step.agent_name,
                            task=step.task,
                            memory_manager=runtime.memory_manager,
                            session_id=context.session_id,
                        )
                    )
                    knowledge_context = knowledge_result.context

                git_context = self._git_service.begin_agent_step(
                    project,
                    step.agent_name,
                )

                step_context = self._build_step_context(
                    team_context,
                    step,
                    git_context=git_context,
                    project=project,
                    knowledge_context=knowledge_context,
                )

                step_result = self._run_step_with_verification(
                    agent=agent,
                    step=step,
                    step_context=step_context,
                    project=project,
                    runtime=runtime,
                    verification_log=verification_log,
                    session_id=context.session_id,
                )

                if not step_result.success:

                    self._update_status(ProjectStatus.FAILED)

                    return PipelineResult(
                        success=False,
                        completed_steps=completed,
                        failed_agent=step.agent_name,
                        error_message=(
                            step_result.content or "Agent step failed"
                        ),
                        metadata={
                            "step_index": index,
                            "verification_log": verification_log,
                        },
                    )

                completed.append(step.agent_name)

                if self._on_agent_finished is not None:

                    self._on_agent_finished(
                        step.agent_name,
                        True,
                        {
                            "execution_time_ms": step_result.metadata.get(
                                "execution_time_ms",
                                0,
                            ),
                            "token_usage": step_result.metadata.get(
                                "token_usage",
                                0,
                            ),
                            "tool_calls": step_result.metadata.get(
                                "tool_calls",
                                0,
                            ),
                        },
                    )

                if self._management_service.enabled:

                    mgmt_context = self._management_service.on_agent_completed(
                        project,
                        step.agent_name,
                        success=True,
                        memory_manager=runtime.memory_manager,
                        session_id=context.session_id,
                    )

                    team_context.shared_context.update(
                        mgmt_context.to_shared_context(),
                    )

                if self._knowledge_service.enabled:

                    self._knowledge_service.update_after_agent(
                        project,
                        agent_name=step.agent_name,
                        success=True,
                        summary=step_result.content[:500] if step_result.content else "",
                        memory_manager=runtime.memory_manager,
                        session_id=context.session_id,
                    )

                commit_info = self._git_service.commit_agent_step(
                    project=project,
                    agent_name=step.agent_name,
                    artifact_manager=self._artifact_manager,
                    memory_manager=runtime.memory_manager,
                    session_id=context.session_id,
                )

                if commit_info is not None:

                    git_log.append({
                        "agent": step.agent_name,
                        "sha": commit_info.sha,
                        "branch": commit_info.branch,
                        "message": commit_info.message,
                    })

                    if self._on_git_event is not None:

                        self._on_git_event(git_log[-1])

                merge_result = self._git_service.merge_agent_to_develop(
                    project=project,
                    agent_name=step.agent_name,
                    memory_manager=runtime.memory_manager,
                    session_id=context.session_id,
                )

                if merge_result is not None:

                    git_log.append({
                        "agent": step.agent_name,
                        "merge": (
                            f"{merge_result.source_branch}->"
                            f"{merge_result.target_branch}"
                        ),
                        "success": merge_result.success,
                        "conflicts": merge_result.conflict_files,
                    })

                    if self._on_git_event is not None:

                        self._on_git_event(git_log[-1])

                    if not merge_result.success:

                        self._update_status(ProjectStatus.FAILED)

                        return PipelineResult(
                            success=False,
                            completed_steps=completed,
                            failed_agent=step.agent_name,
                            error_message=(
                                f"Git merge failed: "
                                f"{merge_result.message}"
                            ),
                            metadata={
                                "step_index": index,
                                "git_log": git_log,
                            },
                        )

                git_context = self._git_service.build_context(project)

            except ArtifactDependencyError as error:

                self._update_status(ProjectStatus.FAILED)

                return PipelineResult(
                    success=False,
                    completed_steps=completed,
                    failed_agent=step.agent_name,
                    error_message=str(error),
                    metadata={"step_index": index},
                )

            except Exception as error:

                self._update_status(ProjectStatus.FAILED)

                return PipelineResult(
                    success=False,
                    completed_steps=completed,
                    failed_agent=step.agent_name,
                    error_message=str(error),
                    metadata={"step_index": index},
                )

        self._update_status(ProjectStatus.DELIVERING)

        finalize = self._git_service.finalize_pipeline(
            project,
            memory_manager=runtime.memory_manager,
            session_id=context.session_id,
        )

        if finalize is not None and not finalize.success:

            self._update_status(ProjectStatus.FAILED)

            return PipelineResult(
                success=False,
                completed_steps=completed,
                failed_agent="GitService",
                error_message=f"Finalize merge failed: {finalize.message}",
                metadata={
                    "git_log": git_log,
                    "artifact_count": self._artifact_manager.count(),
                },
            )

        deployment_log: dict[str, Any] = {}

        if self._deployment_service.enabled:

            deployment_result = self._deployment_service.run_pipeline(
                project,
                artifact_manager=self._artifact_manager,
                memory_manager=runtime.memory_manager,
                session_id=context.session_id,
            )

            deployment_log = {
                "success": deployment_result.success,
                "version": deployment_result.metadata.get("version", ""),
                "deploy_url": (
                    deployment_result.context.deploy_url
                    if deployment_result.context
                    else ""
                ),
                "error": deployment_result.error_message,
            }

            if self._on_deployment_finished is not None:

                self._on_deployment_finished(deployment_log)

            if not deployment_result.success:

                self._update_status(ProjectStatus.FAILED)

                return PipelineResult(
                    success=False,
                    completed_steps=completed,
                    failed_agent="DeploymentService",
                    error_message=(
                        deployment_result.error_message
                        or "Deployment pipeline failed"
                    ),
                    metadata={
                        "artifact_count": self._artifact_manager.count(),
                        "verification_log": verification_log,
                        "git_log": git_log,
                        "deployment_log": deployment_log,
                    },
                )

        else:

            deployment_log = {"skipped": True}

        operations_log: dict[str, Any] = {}

        if (
            self._operations_service.enabled
            and self._settings.operations_after_deploy
            and deployment_log.get("success", deployment_log.get("skipped"))
        ):

            deploy_url = deployment_log.get("deploy_url", "")

            ops_result = self._operations_service.run_pipeline(
                project,
                artifact_manager=self._artifact_manager,
                workspace_manager=self._workspace_manager,
                memory_manager=runtime.memory_manager,
                team_runtime=runtime,
                session_id=context.session_id,
                deploy_url=deploy_url,
            )

            operations_log = {
                "success": ops_result.success,
                "healthy": ops_result.metadata.get("healthy", False),
                "incident_id": ops_result.metadata.get("incident_id", ""),
                "cpu": ops_result.metadata.get("cpu", {"value": 0, "unit": "%"}),
                "memory": ops_result.metadata.get(
                    "memory",
                    {"value": 0, "unit": "MB"},
                ),
                "services": ops_result.metadata.get("services", []),
                "health": ops_result.metadata.get(
                    "health",
                    {"status": "healthy" if ops_result.success else "degraded"},
                ),
                "alerts": ops_result.metadata.get("alerts", []),
                "incidents": ops_result.metadata.get("incidents", []),
            }

            if self._on_operation_update is not None:

                self._on_operation_update(operations_log)

            if not ops_result.success:

                self._update_status(ProjectStatus.FAILED)

                return PipelineResult(
                    success=False,
                    completed_steps=completed,
                    failed_agent="OperationsService",
                    error_message=(
                        ops_result.error_message
                        or "Post-deploy operations failed"
                    ),
                    metadata={
                        "artifact_count": self._artifact_manager.count(),
                        "verification_log": verification_log,
                        "git_log": git_log,
                        "deployment_log": deployment_log,
                        "operations_log": operations_log,
                    },
                )

        elif not self._operations_service.enabled:

            operations_log = {"skipped": True}

        knowledge_log: dict[str, Any] = {}

        if self._knowledge_service.enabled:

            knowledge_result = self._knowledge_service.finalize(
                project,
                artifact_manager=self._artifact_manager,
                memory_manager=runtime.memory_manager,
                session_id=context.session_id,
                pipeline_success=True,
            )

            knowledge_log = {
                "success": knowledge_result.success,
                "entries": knowledge_result.metadata.get("entry_count", 0),
                "report": knowledge_result.report_path,
            }

        elif not self._knowledge_service.enabled:

            knowledge_log = {"skipped": True}

        self._update_status(ProjectStatus.FINISHED)

        return PipelineResult(
            success=True,
            completed_steps=completed,
            metadata={
                "artifact_count": self._artifact_manager.count(),
                "verification_log": verification_log,
                "git_log": git_log,
                "deployment_log": deployment_log,
                "operations_log": operations_log,
                "knowledge_log": knowledge_log,
            },
        )

    def _run_step_with_verification(
        self,
        *,
        agent,
        step: PipelineStep,
        step_context: AgentContext,
        project: Project,
        runtime: TeamAgentRuntime,
        verification_log: list[dict[str, Any]],
        session_id: str = "",
    ) -> AgentResult:

        target = self._registry.get_verification_target(
            step.agent_name,
        )

        verify_enabled = (
            self._settings.enable_verification
            and target is not None
        )

        attempt = 0
        previous_summary = ""
        last_result: AgentResult | None = None

        while True:

            if attempt > 0:

                self._update_status(ProjectStatus.REVIEWING)

            last_result = agent.run(step_context)

            if not last_result.success:

                return last_result

            if not verify_enabled:

                return last_result

            execution_result, verification_result = (
                self._execute_and_verify(
                    project=project,
                    target=target,
                )
            )

            verification_log.append({
                "agent": step.agent_name,
                "target": target,
                "attempt": attempt,
                "execution_success": execution_result.success,
                "verification_success": verification_result.success,
            })

            passed = (
                verification_result.success
                and self._execution_counts_as_passed(
                    target=target,
                    execution_result=execution_result,
                )
            )

            if passed:

                return last_result

            attempt += 1

            if self._management_service.enabled:

                self._management_service.record_verification_failure()

            decision = self._retry_policy.evaluate(
                attempt=attempt,
                verification=verification_result,
                execution=execution_result,
            )

            if not decision.should_retry:

                if self._management_service.enabled:

                    self._management_service.on_agent_completed(
                        project,
                        step.agent_name,
                        success=False,
                        memory_manager=runtime.memory_manager,
                        session_id=session_id,
                    )

                return AgentResult(
                    success=False,
                    model="verification",
                    content=(
                        f"{step.agent_name} 验证失败（"
                        f"已重试 {attempt} 次）:\n"
                        f"{verification_result.summary}\n"
                        f"{execution_result.combined_output[:1000]}"
                    ),
                )

            feedback = self._retry_policy.build_feedback(
                agent_name=step.agent_name,
                target=target,
                attempt=attempt,
                verification=verification_result,
                execution=execution_result,
                previous_summary=previous_summary,
            )

            fix_instruction = (
                self._retry_policy.build_fix_instruction(feedback)
            )

            self._save_fix_memory(
                runtime=runtime,
                session_id=step_context.session_id,
                feedback=feedback,
                fix_instruction=fix_instruction,
            )

            previous_summary = (
                f"Attempt {attempt}: "
                f"{verification_result.error_log[:500]}"
            )

            team_context = CoordinatorContext.from_agent_context(
                context=step_context,
                project=project,
            )

            step_context = self._build_retry_context(
                team_context=team_context,
                step=step,
                feedback=feedback,
                fix_instruction=fix_instruction,
            )

    def _execute_and_verify(
        self,
        *,
        project: Project,
        target: str,
    ) -> tuple[ExecutionResult, VerificationResult]:

        workspace = project.workspace_path

        if "/" in target and not target.startswith(
            ("backend", "frontend", "tests")
        ) or target == "README.md":

            relative = (
                target
                if "/" in target
                else target
            )

            verification = (
                self._verification_manager.verify_document_path(
                    workspace,
                    relative,
                )
            )

            return (
                ExecutionResult(
                    success=verification.success,
                    workspace_path=workspace,
                    target=relative,
                ),
                verification,
            )

        execution = self._execution_manager.execute_target(
            workspace,
            target.split("/")[0]
            if "/" in target
            else target,
        )

        verification = self._verification_manager.verify(
            workspace,
            target=target.split("/")[0]
            if "/" in target
            else target,
            execution_result=execution,
        )

        return execution, verification

    @staticmethod
    def _execution_counts_as_passed(
        *,
        target: str,
        execution_result: ExecutionResult,
    ) -> bool:
        """
        tests/ 不是可执行子项目，execute_target 会返回 not runnable，
        但 pytest 已在 VerificationManager 中单独验证。
        """

        if execution_result.success:

            return True

        root_target = target.split("/")[0]

        if root_target == "tests":

            message = (execution_result.error_message or "").lower()

            return "not runnable" in message

        return False

    def _build_retry_context(
        self,
        *,
        team_context: CoordinatorContext,
        step: PipelineStep,
        feedback,
        fix_instruction: str,
    ) -> AgentContext:

        shared = dict(team_context.shared_context)
        shared.update(feedback.to_shared_context())

        return AgentContext(
            session_id=team_context.session_id,
            user_message=fix_instruction,
            metadata={
                **team_context.metadata,
                "current_task": fix_instruction,
                "pipeline_step": step.agent_name,
                "verification_retry": True,
                "verification_attempt": feedback.attempt,
                "verification_target": feedback.target,
                "verification_error_log": feedback.error_log,
                "verification_result": feedback.verification_summary,
                "execution_result": feedback.execution_summary,
                "previous_attempt": feedback.previous_attempt_summary,
                "fix_instruction": fix_instruction,
            },
            agent_name=step.agent_name,
            agent_role=self._registry.get_role(step.agent_name),
            shared_context=shared,
        )

    @staticmethod
    def _save_fix_memory(
        *,
        runtime: TeamAgentRuntime,
        session_id: str,
        feedback,
        fix_instruction: str,
    ) -> None:

        record = MemoryRecord(
            role="assistant",
            content=(
                f"Fix attempt {feedback.attempt} "
                f"for {feedback.agent_name}:\n"
                f"{feedback.error_log[:1500]}"
            ),
            metadata={
                "type": "memory",
                "category": "fix_attempt",
                "agent": feedback.agent_name,
                "attempt": feedback.attempt,
                "target": feedback.target,
                "fix_instruction": fix_instruction[:2000],
            },
        )

        runtime.memory_manager.memory.save(
            session_id,
            record,
        )

    def _build_step_context(
        self,
        team_context: CoordinatorContext,
        step: PipelineStep,
        *,
        git_context: GitContext | None = None,
        project: Project | None = None,
        knowledge_context=None,
    ) -> AgentContext:

        shared = dict(team_context.shared_context)

        if git_context is not None and git_context.is_initialized:

            shared.update(git_context.to_shared_context())

        if (
            project is not None
            and self._management_service.enabled
        ):

            mgmt_context = self._management_service.build_context(project)

            shared.update(mgmt_context.to_shared_context())

        if knowledge_context is not None:

            shared.update(knowledge_context.to_shared_context())

        metadata = {
            **team_context.metadata,
            "current_task": step.task,
            "pipeline_step": step.agent_name,
        }

        if git_context is not None:

            metadata["git_context"] = git_context.to_prompt_block()

        if project is not None and self._management_service.enabled:

            metadata["management_context"] = True

        if knowledge_context is not None:

            metadata["knowledge_context"] = True

        return AgentContext(
            session_id=team_context.session_id,
            user_message=team_context.user_message,
            metadata=metadata,
            agent_name=step.agent_name,
            agent_role=self._registry.get_role(step.agent_name),
            shared_context=shared,
        )

    def _update_status(
        self,
        status: ProjectStatus,
    ) -> None:

        self._project_service.update_status(status)

        if self._on_status_change is not None:

            self._on_status_change(status)

    @staticmethod
    def _build_success_summary(
        project: Project,
        pipeline_result: PipelineResult,
    ) -> str:

        steps = " → ".join(pipeline_result.completed_steps)
        verify_count = len(
            pipeline_result.metadata.get("verification_log", [])
        )
        git_count = len(
            pipeline_result.metadata.get("git_log", [])
        )
        deployment_log = pipeline_result.metadata.get(
            "deployment_log",
            {},
        )
        deployment_line = ""

        if deployment_log.get("skipped"):

            deployment_line = "\n部署: 已跳过"

        elif deployment_log:

            deployment_line = (
                f"\n部署: {'成功' if deployment_log.get('success') else '失败'}"
                f"\n版本: {deployment_log.get('version', 'n/a')}"
                f"\nURL: {deployment_log.get('deploy_url', 'n/a')}"
            )

        return (
            f"项目「{project.name}」流水线执行完成。\n"
            f"流程: {steps}\n"
            f"Workspace: {project.workspace_path}\n"
            f"产物数量: {pipeline_result.metadata.get('artifact_count', 0)}\n"
            f"验证次数: {verify_count}\n"
            f"Git 操作: {git_count}"
            f"{deployment_line}"
        )
