from dataclasses import dataclass

from app.multi_agent.agent import Agent
from app.multi_agent.profile import AgentProfile


@dataclass
class RegisteredAgent:
    """
    Registry 中的 Agent 条目。
    """

    agent: Agent

    profile: AgentProfile


class AgentRegistry:
    """
    Multi-Agent 注册中心。

    负责注册、删除、查找 Agent，与单 Agent 的 app.agents.registry 解耦。
    """

    def __init__(self):

        self._agents: dict[str, RegisteredAgent] = {}

    def register(
        self,
        agent: Agent,
        profile: AgentProfile | None = None,
    ) -> None:

        if profile is None:

            profile = AgentProfile(
                name=agent.name,
                role="assistant",
                description=f"Agent {agent.name}",
                capabilities=agent.get_capabilities(),
            )

        if profile.name != agent.name:

            profile.name = agent.name

        self._agents[agent.name] = RegisteredAgent(
            agent=agent,
            profile=profile,
        )

    def unregister(
        self,
        name: str,
    ) -> bool:

        if name not in self._agents:

            return False

        del self._agents[name]

        return True

    def get(
        self,
        name: str,
    ) -> RegisteredAgent | None:

        return self._agents.get(name)

    def get_agent(
        self,
        name: str,
    ) -> Agent | None:

        entry = self.get(name)

        if entry is None:

            return None

        return entry.agent

    def get_all(self) -> list[RegisteredAgent]:

        return list(self._agents.values())

    def list_names(self) -> list[str]:

        return list(self._agents.keys())

    def find_by_capability(
        self,
        capability: str,
    ) -> list[RegisteredAgent]:

        return [
            entry
            for entry in self._agents.values()
            if capability in entry.profile.capabilities
        ]

    def find_handlers(
        self,
        task_input: str,
        metadata: dict | None = None,
    ) -> list[RegisteredAgent]:

        return [
            entry
            for entry in self._agents.values()
            if entry.agent.can_handle(
                task_input,
                metadata,
            )
        ]

    def clear(self) -> None:

        self._agents.clear()

    def __len__(self) -> int:

        return len(self._agents)
