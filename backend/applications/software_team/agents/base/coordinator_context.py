from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agents.types import AgentContext

from applications.software_team.project.models.project import Project


@dataclass
class CoordinatorContext:
    """
    Software Team Agent 执行上下文。

    在 Framework AgentContext 之上附加 Project 视图，
    供各专业 Agent 读取项目信息与协作状态。

    由 Coordinator 构建 AgentContext，Agent 侧通过
    ``CoordinatorContext.from_agent_context`` 还原。
    """

    session_id: str

    user_message: str

    project: Project

    metadata: dict[str, Any]

    shared_context: dict[str, Any]

    agent_name: str = ""

    agent_role: str = ""

    @classmethod
    def from_agent_context(
        cls,
        context: AgentContext,
        project: Project,
    ) -> CoordinatorContext:
        """
        从 Framework AgentContext 与 Project 构建 CoordinatorContext。
        """

        return cls(
            session_id=context.session_id,
            user_message=context.user_message,
            project=project,
            metadata=dict(context.metadata),
            shared_context=dict(context.shared_context),
            agent_name=context.agent_name,
            agent_role=context.agent_role,
        )

    @property
    def requirement(self) -> str:
        """
        用户原始需求。
        """

        return self.project.requirement

    @property
    def workspace_path(self) -> str:
        """
        项目工作空间路径。
        """

        return self.project.workspace_path
