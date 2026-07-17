from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
from uuid import uuid4

from app.agents.base_agent import BaseAgent
from app.agents.types import AgentContext
from app.agents.types import AgentResult
from app.llm.types import Message
from app.memory.exceptions import MemoryError
from app.memory.types import MemoryRecord

from applications.software_team.agents.base.coordinator_context import (
    CoordinatorContext,
)
from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.artifact import Artifact
from applications.software_team.project.models.project import Project
from applications.software_team.project.workspace.workspace_manager import (
    WorkspaceManager,
)
from applications.software_team.prompt.team_prompt_builder import (
    TeamPromptBuilder,
)
from applications.software_team.runtime.team_agent_runtime import TeamAgentRuntime
from applications.software_team.tools.context import workspace_path_ctx
from applications.software_team.workflow.artifact_reader import ArtifactReader
from applications.software_team.workflow.dependencies import (
    AgentDependencyRegistry,
)


class BaseTeamAgent(BaseAgent):
    """
    AI Software Team 专业 Agent 基类（P5 智能版）。

    继承 Framework BaseAgent，组合：
    - TeamPromptBuilder → Framework PromptBuilder（含 Memory）
    - TeamAgentRuntime → LLMClient + ToolManager + AgentExecutor
    - ArtifactManager / WorkspaceManager → 产物共享

    Agent Loop：Think → Tool → Observation → Think → Finish
    由 Framework AgentExecutor 驱动，不在子类重复实现。
    """

    def __init__(
        self,
        project: Project,
        artifact_manager: ArtifactManager,
        workspace_manager: WorkspaceManager,
        team_prompt_builder: TeamPromptBuilder | None = None,
        team_agent_runtime: TeamAgentRuntime | None = None,
        dependency_registry: AgentDependencyRegistry | None = None,
        artifact_reader: ArtifactReader | None = None,
    ):

        super().__init__()

        self._project = project
        self._artifact_manager = artifact_manager
        self._workspace_manager = workspace_manager
        self._dependency_registry = (
            dependency_registry or AgentDependencyRegistry()
        )
        self._artifact_reader = artifact_reader or ArtifactReader()

        self._runtime = team_agent_runtime or TeamAgentRuntime()

        self._team_prompt_builder = (
            team_prompt_builder
            or TeamPromptBuilder(
                dependency_registry=self._dependency_registry,
                artifact_reader=self._artifact_reader,
                config=self._runtime.config,
                memory_manager=self._runtime.memory_manager,
                tracer=self._runtime.tracer,
            )
        )

    @property
    def project(self) -> Project:

        return self._project

    @property
    def artifact_manager(self) -> ArtifactManager:

        return self._artifact_manager

    @property
    def workspace_manager(self) -> WorkspaceManager:

        return self._workspace_manager

    @property
    def runtime(self) -> TeamAgentRuntime:

        return self._runtime

    @property
    @abstractmethod
    def agent_name(self) -> str:

        """
        Agent 标识，用于 Artifact.owner 与日志。
        """

    def before_run(
        self,
        context: AgentContext,
    ) -> None:
        """
        执行前：绑定 Workspace 上下文，供 Tool 使用。
        """

        workspace_path_ctx.set(self._project.workspace_path)

    def execute(
        self,
        context: AgentContext,
    ) -> AgentResult:

        team_context = CoordinatorContext.from_agent_context(
            context=context,
            project=self._project,
        )

        return self.execute_team(team_context)

    @abstractmethod
    def execute_team(
        self,
        context: CoordinatorContext,
    ) -> AgentResult:

        """
        专业 Agent 执行入口。
        """

    def _run_intelligent_loop(
        self,
        context: CoordinatorContext,
        *,
        task_instruction: str | None = None,
    ) -> AgentResult:
        """
        通过 Framework Agent Loop 执行智能任务。

        P6：若 metadata 含 fix_instruction（验证失败重试），
        自动注入 Verification Feedback 到 Prompt。

        流程：Generate → (Execute/Verify 由 Pipeline 负责) →
              Think → Tool → Observation → Finish
        """

        instruction = (
            task_instruction
            or context.metadata.get("fix_instruction")
        )

        try:

            messages = self._build_team_messages(
                context,
                task_instruction=instruction,
            )

        except MemoryError as error:

            return AgentResult(
                success=False,
                model="",
                content=f"Memory error: {error}",
            )

        agent_context = self._build_agent_context_for_loop(
            context,
            task_instruction=instruction,
        )

        self._runtime.tracer.on_prompt(messages)

        result = self._runtime.agent_executor.run(
            agent_context,
            messages,
        )

        if result.success and result.content:

            memory_tag = (
                "fix_attempt"
                if context.metadata.get("verification_retry")
                else "completion"
            )

            self._save_team_memory(
                session_id=context.session_id,
                content=result.content,
                summary=(
                    f"{self.agent_name} [{memory_tag}]: "
                    f"{result.content[:500]}"
                ),
                category=memory_tag,
            )

        return result

    def _build_agent_context_for_loop(
        self,
        context: CoordinatorContext,
        *,
        task_instruction: str | None = None,
    ) -> AgentContext:
        """
        构建传给 AgentExecutor 的 AgentContext。
        """

        instruction = (
            task_instruction
            or context.metadata.get("fix_instruction")
            or self._dependency_registry.get_task_instruction(
                self.agent_name,
            )
        )

        return AgentContext(
            session_id=context.session_id,
            user_message=instruction,
            metadata={
                **context.metadata,
                "team_agent": self.agent_name,
                "project_id": self._project.id,
                "workspace_path": self._project.workspace_path,
            },
            agent_name=self.agent_name,
            agent_role=self._dependency_registry.get_role(
                self.agent_name,
            ),
            shared_context={
                **context.shared_context,
                "project_name": self._project.name,
                "workspace_path": self._project.workspace_path,
            },
        )

    def _build_team_messages(
        self,
        context: CoordinatorContext,
        *,
        task_instruction: str | None = None,
    ) -> list[Message]:

        return self._team_prompt_builder.build(
            agent_name=self.agent_name,
            context=context,
            artifact_manager=self._artifact_manager,
            task_instruction=task_instruction,
        )

    def _save_team_memory(
        self,
        *,
        session_id: str,
        content: str,
        summary: str,
        category: str = "completion",
    ) -> None:
        """
        将 Agent 重要产出写入 Memory（type=memory）。
        """

        record = MemoryRecord(
            role="assistant",
            content=summary,
            metadata={
                "type": "memory",
                "category": category,
                "agent": self.agent_name,
                "project_id": self._project.id,
                "artifact_preview": content[:2000],
            },
        )

        self.memory.memory.save(
            session_id,
            record,
        )

    def after_run(
        self,
        context: AgentContext,
        result: AgentResult,
    ) -> None:
        """
        执行后：持久化对话记录到 Memory。
        """

        super().after_run(context, result)

    def _verify_dependencies(self) -> None:
        """
        校验当前 Agent 的产物依赖是否满足。
        """

        dependencies = self._dependency_registry.get_dependencies(
            self.agent_name,
        )

        self._artifact_reader.verify_dependencies(
            dependencies,
            self._artifact_manager,
            self._project.workspace_path,
        )

    def _get_dependency_content(
        self,
        key: str,
    ) -> str:
        """
        从 ArtifactManager 读取单个依赖产物内容。
        """

        resolved = self._artifact_reader.resolve_dependencies(
            (key,),
            self._artifact_manager,
            self._project.workspace_path,
        )

        return resolved.get(key, "")

    def _create_artifact(
        self,
        *,
        name: str,
        artifact_type: str,
        relative_path: str,
        owner: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Artifact:

        workspace = Path(self._project.workspace_path)

        return Artifact(
            id=f"artifact_{uuid4().hex[:12]}",
            name=name,
            type=artifact_type,
            path=str(workspace / relative_path),
            owner=owner or self.agent_name,
            metadata=metadata or {},
        )

    def _save_artifact(
        self,
        artifact: Artifact,
        content: str,
    ) -> Artifact:

        file_path = Path(artifact.path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(
            content,
            encoding=DEFAULT_ENCODING,
        )

        self._artifact_manager.add(artifact)
        self._project.add_artifact(artifact.id)

        return artifact

    def _save_directory_artifact(
        self,
        *,
        directory_name: str,
        files: dict[str, str],
        metadata: dict[str, str] | None = None,
    ) -> Artifact:
        """
        保存目录型产物并注册到 ArtifactManager。
        """

        workspace = Path(self._project.workspace_path)
        directory = workspace / directory_name

        for relative_path, content in files.items():

            file_path = directory / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding=DEFAULT_ENCODING)

        artifact = Artifact(
            id=f"artifact_{uuid4().hex[:12]}",
            name=directory_name,
            type="directory",
            path=str(directory),
            owner=self.agent_name,
            metadata=metadata or {},
        )

        self._artifact_manager.add(artifact)
        self._project.add_artifact(artifact.id)

        return artifact

    def _register_file_artifact(
        self,
        *,
        name: str,
        relative_path: str,
        artifact_type: str = "document",
        metadata: dict[str, str] | None = None,
    ) -> Artifact:
        """
        注册 Workspace 内已存在的文件为 Artifact。
        """

        workspace = Path(self._project.workspace_path)
        file_path = workspace / relative_path

        artifact = Artifact(
            id=f"artifact_{uuid4().hex[:12]}",
            name=name,
            type=artifact_type,
            path=str(file_path),
            owner=self.agent_name,
            metadata=metadata or {},
        )

        self._artifact_manager.add(artifact)
        self._project.add_artifact(artifact.id)

        return artifact

    def _register_directory_artifact(
        self,
        *,
        directory_name: str,
        metadata: dict[str, str] | None = None,
    ) -> Artifact:
        """
        注册 Workspace 内已存在的目录为 Artifact。
        """

        workspace = Path(self._project.workspace_path)
        directory = workspace / directory_name

        artifact = Artifact(
            id=f"artifact_{uuid4().hex[:12]}",
            name=directory_name,
            type="directory",
            path=str(directory),
            owner=self.agent_name,
            metadata=metadata or {},
        )

        self._artifact_manager.add(artifact)
        self._project.add_artifact(artifact.id)

        return artifact

    def _finalize_file_artifact(
        self,
        *,
        result: AgentResult,
        relative_path: str,
        name: str,
        artifact_type: str = "document",
        metadata: dict[str, str] | None = None,
    ) -> tuple[Artifact | None, str]:
        """
        智能 Loop 完成后，确保文件产物存在并注册 Artifact。

        优先读取 LLM 通过 write_file 写入的文件；
        若文件不存在则使用 result.content 回写。
        """

        workspace = Path(self._project.workspace_path)
        file_path = workspace / relative_path

        if file_path.is_file():

            content = file_path.read_text(
                encoding=DEFAULT_ENCODING,
            )

        elif result.content.strip():

            artifact = self._create_artifact(
                name=name,
                artifact_type=artifact_type,
                relative_path=relative_path,
                metadata=metadata,
            )

            self._save_artifact(
                artifact=artifact,
                content=result.content,
            )

            return artifact, result.content

        else:

            return None, ""

        artifact = self._register_file_artifact(
            name=name,
            relative_path=relative_path,
            artifact_type=artifact_type,
            metadata=metadata,
        )

        return artifact, content

    def _recover_existing_file_artifact(
        self,
        *,
        relative_path: str,
        name: str,
        artifact_type: str = "document",
        metadata: dict[str, str] | None = None,
        min_chars: int = 200,
    ) -> AgentResult | None:
        """
        Loop 失败时，若目标文件已由 Tool 写入，则直接注册产物并视为成功。
        """

        workspace = Path(self._project.workspace_path)
        file_path = workspace / relative_path

        if not file_path.is_file():

            return None

        content = file_path.read_text(encoding=DEFAULT_ENCODING).strip()

        if len(content) < min_chars:

            return None

        artifact = self._register_file_artifact(
            name=name,
            relative_path=relative_path,
            artifact_type=artifact_type,
            metadata={
                **(metadata or {}),
                "source": "partial_recovery",
            },
        )

        return AgentResult(
            success=True,
            model="partial_recovery",
            content=(
                f"{name} 已从 Workspace 恢复（{len(content)} chars）\n\n"
                f"{content[:500]}"
            ),
        )

    def _finalize_directory_artifact(
        self,
        *,
        directory_name: str,
        metadata: dict[str, str] | None = None,
    ) -> Artifact | None:
        """
        注册 LLM 通过 write_file 写入的目录产物。
        """

        workspace = Path(self._project.workspace_path)
        directory = workspace / directory_name

        if not directory.is_dir():

            return None

        files = [
            path
            for path in directory.rglob("*")
            if path.is_file()
        ]

        if not files:

            return None

        return self._register_directory_artifact(
            directory_name=directory_name,
            metadata=metadata,
        )

    def get_docs_dir(self) -> Path:

        return Path(self._project.workspace_path) / "docs"

    def get_workspace_subdir(
        self,
        folder: str,
    ) -> Path:

        return self._workspace_manager.get_subdirectory(
            self._project.name,
            folder,
        )
