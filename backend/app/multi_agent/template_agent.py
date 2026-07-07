from typing import Any

from app.agents.types import AgentContext
from app.agents.types import AgentResult
from app.multi_agent.agent import Agent
from app.multi_agent.profile import AgentProfile


class TemplateAgent(Agent):
    """
    模板 Agent，用于示例与测试，无需调用 LLM。
    """

    def __init__(
        self,
        profile: AgentProfile,
        template: str,
    ):

        self._profile = profile
        self._template = template

    @property
    def name(self) -> str:

        return self._profile.name

    @property
    def profile(self) -> AgentProfile:

        return self._profile

    def run(
        self,
        context: AgentContext,
    ) -> AgentResult:

        content = self._template.format(
            input=context.user_message,
            goal=context.metadata.get(
                "root_goal",
                context.user_message,
            ),
            task=context.metadata.get(
                "current_task",
                context.user_message,
            ),
            shared=context.shared_context,
        )

        return AgentResult(
            success=True,
            model="template",
            content=content,
        )

    def can_handle(
        self,
        task_input: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:

        lower_input = task_input.lower()

        for keyword in self._profile.keywords:

            if keyword.lower() in lower_input:

                return True

        task_type = (metadata or {}).get("task_type", "")

        return task_type in self._profile.capabilities

    def get_capabilities(self) -> list[str]:

        return list(self._profile.capabilities)
