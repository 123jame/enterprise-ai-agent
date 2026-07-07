from typing import Any
from typing import Callable

from app.agents.base_agent import BaseAgent
from app.agents.types import AgentContext
from app.agents.types import AgentResult
from app.multi_agent.agent import Agent


class BaseAgentAdapter(Agent):
    """
    将已有 BaseAgent 子类适配为 Multi-Agent Agent。

    无需修改现有 Agent 代码即可接入 Multi-Agent Runtime。
    """

    def __init__(
        self,
        agent: BaseAgent,
        name: str,
        capabilities: list[str] | None = None,
        can_handle: Callable[
            [str, dict[str, Any] | None],
            bool,
        ] | None = None,
    ):

        self._agent = agent
        self._name = name
        self._capabilities = capabilities or ["chat"]
        self._can_handle_fn = can_handle

    @property
    def name(self) -> str:
        return self._name

    def run(
        self,
        context: AgentContext,
    ) -> AgentResult:

        return self._agent.run(context)

    def can_handle(
        self,
        task_input: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:

        if self._can_handle_fn is not None:

            return self._can_handle_fn(
                task_input,
                metadata,
            )

        return True

    def get_capabilities(self) -> list[str]:

        return list(self._capabilities)
