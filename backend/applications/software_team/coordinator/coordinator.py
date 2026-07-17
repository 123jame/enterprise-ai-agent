from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Protocol
from uuid import uuid4

from app.agents.types import AgentContext
from app.agents.types import AgentResult

from applications.software_team.config.defaults import DEFAULT_TECH_STACK
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.artifact import Artifact
from applications.software_team.project.models.project import Project
from applications.software_team.project.models.project_status import ProjectStatus
from applications.software_team.project.services.project_service import (
    ProjectService,
)
from applications.software_team.project.workspace.workspace_manager import (
    WorkspaceManager,
)
from applications.software_team.execution.execution_manager import ExecutionManager
from applications.software_team.execution.verification_manager import (
    VerificationManager,
)
from applications.software_team.git.git_service import GitService
from applications.software_team.deployment.deployment_service import DeploymentService
from applications.software_team.operations.operations_service import OperationsService
from applications.software_team.management.management_service import ManagementService
from applications.software_team.knowledge.knowledge_service import KnowledgeService
from applications.software_team.workflow.pipeline import SoftwareTeamPipeline


@dataclass
class CoordinatorResult:
    """
    SoftwareTeamCoordinator 执行结果。

    封装项目、产物与最终输出，作为应用层对外返回结构。
    """

    success: bool

    project: Project

    content: str

    artifacts: list[Artifact] = field(
        default_factory=list,
    )

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


class SoftwareTeamWorkflowRunner(Protocol):
    """
    Software Team Workflow 运行器协议。

    后续阶段注入具体 Workflow 实现，Coordinator 不依赖具体 Agent 或 Tool。
    """

    def run(
        self,
        context: AgentContext,
        project: Project,
    ) -> AgentResult:
        """
        执行软件开发工作流并返回 Framework AgentResult。
        """


class SoftwareTeamCoordinator:
    """
    AI Software Development Team 总协调器。

    职责：
    - 接收用户需求
    - 创建 Project 与 Workspace
    - 构建 AgentContext
    - 委托 Workflow Pipeline 顺序调度各专业 Agent
    - 执行与验证重试（P6 ExecutionManager / VerificationManager）
    - 运维监控与故障处理（P9 OperationsService）
    - 项目管理与进度跟踪（P10 ManagementService）
    - 知识管理与持续改进（P11 KnowledgeService）
    - 管理 ProjectStatus
    - 收集 Artifact 并返回最终结果

    不负责：
    - Tool Calling / Prompt 构建 / Memory / MCP / LLM 调用
    以上能力均由已有 Enterprise AI Agent Framework 提供。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        project_service: ProjectService | None = None,
        workspace_manager: WorkspaceManager | None = None,
        artifact_manager: ArtifactManager | None = None,
        workflow_runner: SoftwareTeamWorkflowRunner | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()

        self._workspace_manager = (
            workspace_manager
            or WorkspaceManager(
                workspace_root=str(
                    self._settings.workspace_root
                ),
            )
        )

        self._artifact_manager = (
            artifact_manager or ArtifactManager()
        )

        self._project_service = (
            project_service
            or ProjectService(
                workspace_manager=self._workspace_manager,
                artifact_manager=self._artifact_manager,
            )
        )

        self._operations_service = OperationsService(
            settings=self._settings,
        )

        self._management_service = ManagementService(
            settings=self._settings,
        )
        self._management_service.bind_project_service(
            self._project_service,
        )

        self._knowledge_service = KnowledgeService(
            settings=self._settings,
        )

        self._workflow_runner = workflow_runner or SoftwareTeamPipeline(
            project_service=self._project_service,
            artifact_manager=self._artifact_manager,
            workspace_manager=self._workspace_manager,
            settings=self._settings,
            execution_manager=ExecutionManager(
                settings=self._settings,
            ),
            verification_manager=VerificationManager(
                settings=self._settings,
            ),
            git_service=GitService(
                settings=self._settings,
            ),
            deployment_service=DeploymentService(
                settings=self._settings,
            ),
            management_service=self._management_service,
            knowledge_service=self._knowledge_service,
        )

    @property
    def project_service(self) -> ProjectService:
        """
        暴露 ProjectService，便于测试与扩展。
        """

        return self._project_service

    @property
    def artifact_manager(self) -> ArtifactManager:
        """
        暴露 ArtifactManager，便于测试与扩展。
        """

        return self._artifact_manager

    def run(
        self,
        *,
        session_id: str,
        user_requirement: str,
        project_name: str | None = None,
    ) -> CoordinatorResult:
        """
        执行一次完整的 Software Team 协调流程。

        参数:
            session_id: 会话标识，传入 Framework AgentContext。
            user_requirement: 用户原始需求，例如「开发一个图书管理系统」。
            project_name: 可选项目名称；未提供时从需求推断。

        返回:
            CoordinatorResult，包含 Project、Artifact 与最终输出。
        """

        project = self._create_project(
            user_requirement=user_requirement,
            project_name=project_name,
        )

        try:

            from applications.software_team.runtime.team_agent_runtime import (
                TeamAgentRuntime,
            )

            runtime = TeamAgentRuntime(settings=self._settings)

            planning_result = None

            if self._management_service.enabled:

                planning_result = self._management_service.run_planning(
                    project,
                    artifact_manager=self._artifact_manager,
                    memory_manager=runtime.memory_manager,
                    session_id=session_id,
                )

                if not planning_result.success:

                    return self._collect_result(
                        project=project,
                        workflow_result=AgentResult(
                            success=False,
                            model="management",
                            content=(
                                planning_result.error_message
                                or "Project planning failed"
                            ),
                        ),
                    )

            self._project_service.update_status(
                ProjectStatus.PLANNING
            )

            context = self._build_context(
                session_id=session_id,
                project=project,
                user_requirement=user_requirement,
            )

            if (
                planning_result is not None
                and planning_result.context is not None
            ):

                context.shared_context.update(
                    planning_result.context.to_shared_context(),
                )
                context.metadata["management_context"] = True

            workflow_result = self._execute_workflow(
                context=context,
                project=project,
            )

            management_metadata: dict[str, Any] = {}

            if self._management_service.enabled:

                finalize_result = self._management_service.finalize(
                    project,
                    artifact_manager=self._artifact_manager,
                    memory_manager=runtime.memory_manager,
                    session_id=session_id,
                    pipeline_success=workflow_result.success,
                )

                management_metadata = {
                    "delivery_score": finalize_result.metadata.get(
                        "delivery_score",
                        0,
                    ),
                    "progress": (
                        finalize_result.progress.summary
                        if finalize_result.progress
                        else ""
                    ),
                    "risks": (
                        finalize_result.risks.summary
                        if finalize_result.risks
                        else ""
                    ),
                }

                if workflow_result.success and finalize_result.delivery:

                    delivery = finalize_result.delivery
                    delivery_note = (
                        f"\n\n## Delivery Evaluation\n"
                        f"{delivery.summary}"
                    )

                    if not delivery.success:

                        delivery_note += (
                            "\n\n(Delivery score below threshold; "
                            "pipeline artifacts were still generated.)"
                        )

                    workflow_result = AgentResult(
                        success=workflow_result.success,
                        model=workflow_result.model,
                        content=f"{workflow_result.content}{delivery_note}",
                    )

            return self._collect_result(
                project=project,
                workflow_result=workflow_result,
                extra_metadata={
                    "management": management_metadata,
                },
            )

        except Exception as error:

            self._project_service.update_status(
                ProjectStatus.FAILED
            )

            return self._collect_result(
                project=project,
                workflow_result=AgentResult(
                    success=False,
                    model="",
                    content=str(error),
                ),
            )

    def run_operations(
        self,
        *,
        session_id: str,
        project_name: str | None = None,
        workspace_path: str | None = None,
        deploy_url: str = "",
        force_maintenance: bool = False,
    ) -> CoordinatorResult:
        """
        执行运维监控流水线（P9）。

        Monitor → Alert → Diagnosis → Maintenance → Agent → Verify → Redeploy
        """

        project = self._resolve_project(
            project_name=project_name,
            workspace_path=workspace_path,
        )

        if project is None:

            return CoordinatorResult(
                success=False,
                project=Project(
                    id="",
                    name=project_name or "",
                    requirement="",
                    workspace_path=workspace_path or "",
                    status=ProjectStatus.FAILED,
                ),
                content="No project found for operations run.",
                metadata={"error": "project_not_found"},
            )

        try:

            from applications.software_team.runtime.team_agent_runtime import (
                TeamAgentRuntime,
            )

            runtime = TeamAgentRuntime(settings=self._settings)

            ops_result = self._operations_service.run_pipeline(
                project,
                artifact_manager=self._artifact_manager,
                workspace_manager=self._workspace_manager,
                memory_manager=runtime.memory_manager,
                team_runtime=runtime,
                session_id=session_id,
                deploy_url=deploy_url,
                force_maintenance=force_maintenance,
            )

            content = self._build_operations_summary(ops_result)

            return self._collect_result(
                project=project,
                workflow_result=AgentResult(
                    success=ops_result.success,
                    model="operations",
                    content=content,
                ),
                extra_metadata={
                    "operations": {
                        "healthy": ops_result.metadata.get("healthy", False),
                        "incident_id": ops_result.metadata.get("incident_id", ""),
                        "task_count": ops_result.metadata.get("task_count", 0),
                    },
                },
            )

        except Exception as error:

            return self._collect_result(
                project=project,
                workflow_result=AgentResult(
                    success=False,
                    model="operations",
                    content=str(error),
                ),
            )

    def _resolve_project(
        self,
        *,
        project_name: str | None,
        workspace_path: str | None,
    ) -> Project | None:
        """
        解析运维目标项目：优先当前 ProjectService，其次 workspace 路径。
        """

        current = self._project_service.get_project()

        if current is not None:

            if project_name and current.name != project_name:

                pass

            else:

                return current

        if workspace_path:

            from pathlib import Path

            path = Path(workspace_path).resolve()
            name = project_name or path.name

            return Project(
                id=str(uuid4()),
                name=name,
                requirement="operations",
                description="Operations target project",
                workspace_path=str(path),
                status=ProjectStatus.FINISHED,
            )

        if project_name:

            workspace = self._workspace_manager.get_workspace(
                project_name,
            )

            if workspace.exists():

                return Project(
                    id=str(uuid4()),
                    name=project_name,
                    requirement="operations",
                    workspace_path=str(workspace),
                    status=ProjectStatus.FINISHED,
                )

        return None

    @staticmethod
    def _build_operations_summary(ops_result) -> str:

        if ops_result.metadata.get("skipped"):

            return "Operations pipeline skipped (enable_operations=false)."

        if ops_result.metadata.get("healthy"):

            return (
                "Operations: system healthy, no alerts.\n"
                f"{ops_result.monitor.summary if ops_result.monitor else ''}"
            )

        lines = [
            "Operations pipeline completed.",
            f"Alerts: {len(ops_result.alerts.alerts) if ops_result.alerts else 0}",
        ]

        if ops_result.incident and ops_result.incident.incident:

            lines.append(
                f"Incident: {ops_result.incident.incident.title}"
            )

        if ops_result.diagnosis:

            lines.append(f"Diagnosis: {ops_result.diagnosis.summary[:300]}")

        if ops_result.maintenance:

            lines.append(
                f"Maintenance tasks: {len(ops_result.maintenance.tasks)}"
            )
            lines.append(
                f"Auto fix verification: "
                f"{'PASS' if ops_result.maintenance.verification_passed else 'FAIL'}"
            )

        return "\n".join(lines)

    def _create_project(
        self,
        *,
        user_requirement: str,
        project_name: str | None,
    ) -> Project:
        """
        根据用户需求创建 Project 并初始化 Workspace。

        ProjectService 内部会调用 WorkspaceManager 创建标准目录结构。
        """

        name = project_name or self._infer_project_name(
            user_requirement
        )

        project = self._project_service.create_project(
            name=name,
            requirement=user_requirement,
            description=user_requirement,
        )

        if not project.tech_stack:

            project.tech_stack = list(DEFAULT_TECH_STACK)

        return project

    def _build_context(
        self,
        *,
        session_id: str,
        project: Project,
        user_requirement: str,
    ) -> AgentContext:
        """
        构建 Framework AgentContext。

        将 Project 信息写入 metadata 与 shared_context，
        供后续 PromptBuilder / Workflow / Agent 复用。
        """

        shared_context: dict[str, Any] = {
            "project_id": project.id,
            "project_name": project.name,
            "workspace_path": project.workspace_path,
            "requirement": project.requirement,
            "status": project.status.value,
            "tech_stack": project.tech_stack,
        }

        return AgentContext(
            session_id=session_id,
            user_message=user_requirement,
            metadata={
                "application": "software_team",
                "current_task": user_requirement,
                "root_goal": user_requirement,
                "project_id": project.id,
                "project_name": project.name,
                "workspace_path": project.workspace_path,
            },
            agent_name="SoftwareTeamCoordinator",
            agent_role="coordinator",
            shared_context=shared_context,
        )

    def _execute_workflow(
        self,
        *,
        context: AgentContext,
        project: Project,
    ) -> AgentResult:
        """
        委托 Workflow 执行 Agent 调度。

        默认注入 SoftwareTeamPipeline，按 Product → Architect →
        Backend → Frontend → QA → Documentation 顺序执行。
        """

        return self._workflow_runner.run(
            context=context,
            project=project,
        )

    def _collect_result(
        self,
        *,
        project: Project,
        workflow_result: AgentResult,
        extra_metadata: dict[str, Any] | None = None,
    ) -> CoordinatorResult:
        """
        收集 Artifact 并组装 CoordinatorResult。

        从 ArtifactManager 读取产物，同步到 Project.artifacts 字段。
        """

        current_project = (
            self._project_service.get_project()
            or project
        )

        artifacts = self._artifact_manager.list()

        current_project.artifacts = [
            artifact.id
            for artifact in artifacts
        ]

        return CoordinatorResult(
            success=workflow_result.success,
            project=current_project,
            content=workflow_result.content or "",
            artifacts=artifacts,
            metadata={
                "artifact_count": len(artifacts),
                "workspace_path": current_project.workspace_path,
                "project_status": current_project.status.value,
                **(extra_metadata or {}),
                **_extract_workflow_failure_metadata(workflow_result),
            },
        )

    @staticmethod
    def _infer_project_name(
        requirement: str,
    ) -> str:
        """
        从用户需求推断项目名称。

        后续可替换为 LLM 或 ProductAgent 生成，本阶段使用简单规则。
        """

        text = requirement.strip()

        for prefix in (
            "开发一个",
            "开发一套",
            "做一个",
            "构建一个",
            "帮我开发",
        ):

            if text.startswith(prefix):

                text = text[len(prefix):].strip()

                break

        if not text:

            return f"software_project_{uuid4().hex[:8]}"

        return text


def _extract_workflow_failure_metadata(
    workflow_result: AgentResult,
) -> dict[str, str]:

    if workflow_result.success:

        return {}

    match = re.search(
        r"Pipeline 在 (\S+) 失败",
        workflow_result.content or "",
    )

    if match is None:

        return {}

    return {"failed_agent": match.group(1)}
