from __future__ import annotations

from applications.software_team.agents.architect.architect_agent import (
    ArchitectAgent,
)
from applications.software_team.agents.backend.backend_agent import BackendAgent
from applications.software_team.agents.base.base_team_agent import BaseTeamAgent
from applications.software_team.agents.documentation.documentation_agent import (
    DocumentationAgent,
)
from applications.software_team.agents.frontend.frontend_agent import FrontendAgent
from applications.software_team.agents.product.product_agent import ProductAgent
from applications.software_team.agents.qa.qa_agent import QAAgent
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.project import Project
from applications.software_team.project.workspace.workspace_manager import (
    WorkspaceManager,
)
from applications.software_team.prompt.team_prompt_builder import TeamPromptBuilder
from applications.software_team.runtime.team_agent_runtime import TeamAgentRuntime


class TeamAgentFactory:
    """
    专业 Agent 工厂。

    统一创建 Agent 实例，注入共享 Runtime / Project / Manager。
    """

    _AGENT_CLASSES: dict[str, type[BaseTeamAgent]] = {
        "ProductAgent": ProductAgent,
        "ArchitectAgent": ArchitectAgent,
        "BackendAgent": BackendAgent,
        "FrontendAgent": FrontendAgent,
        "QAAgent": QAAgent,
        "DocumentationAgent": DocumentationAgent,
    }

    def __init__(
        self,
        project: Project,
        artifact_manager: ArtifactManager,
        workspace_manager: WorkspaceManager,
        team_agent_runtime: TeamAgentRuntime | None = None,
        team_prompt_builder: TeamPromptBuilder | None = None,
    ):

        self._project = project
        self._artifact_manager = artifact_manager
        self._workspace_manager = workspace_manager
        self._runtime = team_agent_runtime or TeamAgentRuntime()

        self._team_prompt_builder = (
            team_prompt_builder
            or TeamPromptBuilder(
                config=self._runtime.config,
                memory_manager=self._runtime.memory_manager,
                tracer=self._runtime.tracer,
            )
        )

    @property
    def runtime(self) -> TeamAgentRuntime:

        return self._runtime

    def create(
        self,
        agent_name: str,
    ) -> BaseTeamAgent:

        agent_cls = self._AGENT_CLASSES.get(agent_name)

        if agent_cls is None:

            raise ValueError(
                f"Unknown team agent: {agent_name}"
            )

        return agent_cls(
            project=self._project,
            artifact_manager=self._artifact_manager,
            workspace_manager=self._workspace_manager,
            team_prompt_builder=self._team_prompt_builder,
            team_agent_runtime=self._runtime,
        )

    def register(
        self,
        agent_name: str,
        agent_cls: type[BaseTeamAgent],
    ) -> None:

        self._AGENT_CLASSES[agent_name] = agent_cls

    @classmethod
    def supported_agents(cls) -> tuple[str, ...]:

        return tuple(cls._AGENT_CLASSES.keys())
