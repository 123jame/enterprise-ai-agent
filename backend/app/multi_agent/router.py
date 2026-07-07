from abc import ABC
from abc import abstractmethod

from app.multi_agent.agent import Agent
from app.multi_agent.registry import AgentRegistry
from app.multi_agent.registry import RegisteredAgent


class AgentRouter(ABC):
    """
    Agent 路由器抽象。

    预留 LLMRouter 等实现。
    """

    @abstractmethod
    def route(
        self,
        task_input: str,
        registry: AgentRegistry,
        metadata: dict | None = None,
    ) -> Agent | None:
        pass


class RuleBasedRouter(AgentRouter):
    """
    基于规则的路由器。

    按关键词、capabilities 与 can_handle 评分选择 Agent。
    """

    def route(
        self,
        task_input: str,
        registry: AgentRegistry,
        metadata: dict | None = None,
    ) -> Agent | None:

        candidates = registry.find_handlers(
            task_input,
            metadata,
        )

        if not candidates:

            all_entries = registry.get_all()

            if metadata and metadata.get("task_type"):

                typed = [
                    entry
                    for entry in all_entries
                    if metadata["task_type"]
                    in entry.profile.capabilities
                ]

                if typed:

                    return typed[0].agent

            if not all_entries:

                return None

            return all_entries[0].agent

        if len(candidates) == 1:

            return candidates[0].agent

        scored = [
            (
                self._score(
                    entry,
                    task_input,
                    metadata,
                ),
                entry,
            )
            for entry in candidates
        ]

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return scored[0][1].agent

    @staticmethod
    def _score(
        entry: RegisteredAgent,
        task_input: str,
        metadata: dict | None = None,
    ) -> int:

        score = 0
        lower_input = task_input.lower()

        task_type = (metadata or {}).get(
            "task_type",
            "",
        )

        if task_type in entry.profile.capabilities:

            score += 10

        for keyword in entry.profile.keywords:

            if keyword.lower() in lower_input:

                score += 3

        for capability in entry.profile.capabilities:

            if capability.lower() in lower_input:

                score += 2

        if entry.profile.role.lower() in lower_input:

            score += 1

        return score


class LLMRouter(AgentRouter):
    """
    LLM 路由器（预留）。
    """

    def route(
        self,
        task_input: str,
        registry: AgentRegistry,
        metadata: dict | None = None,
    ) -> Agent | None:

        fallback = RuleBasedRouter()

        return fallback.route(
            task_input,
            registry,
            metadata,
        )


def create_router(
    router_type: str,
) -> AgentRouter:

    routers = {
        "rule": RuleBasedRouter,
        "llm": LLMRouter,
    }

    router_cls = routers.get(
        router_type,
        RuleBasedRouter,
    )

    return router_cls()
