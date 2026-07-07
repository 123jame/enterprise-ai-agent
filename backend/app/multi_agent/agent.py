from abc import ABC
from abc import abstractmethod
from typing import Any

from app.agents.types import AgentContext
from app.agents.types import AgentResult


class Agent(ABC):
    """
    Multi-Agent Runtime 统一 Agent 接口。

    与 BaseAgent 解耦：BaseAgent 负责单 Agent 生命周期，
    Agent 接口负责 Multi-Agent 协作（路由、能力发现、任务分配）。

    所有 Multi-Agent 组件只依赖本接口，不直接依赖 ChatAgent。
    """

    @property
    def name(self) -> str:
        """
        Agent 标识，Multi-Agent 注册与路由时使用。
        """

        return type(self).__name__

    @abstractmethod
    def run(
        self,
        context: AgentContext,
    ) -> AgentResult:
        """
        执行任务并返回结果。
        """

    @abstractmethod
    def can_handle(
        self,
        task_input: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        判断当前 Agent 是否能处理该任务。
        """

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """
        返回 Agent 能力标签，供 Router 匹配。
        """
