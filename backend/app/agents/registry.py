from typing import Type

from app.agents.base_agent import BaseAgent


class AgentRegistry:
    """
    Agent 注册中心
    """

    def __init__(self):

        self._agents: dict[str, Type[BaseAgent]] = {}

    def register(
        self,
        name: str,
        agent_cls: Type[BaseAgent]
    ):

        self._agents[name] = agent_cls

    def get(
        self,
        name: str
    ) -> Type[BaseAgent]:

        if name not in self._agents:

            raise ValueError(
                f"Agent '{name}' not found."
            )

        return self._agents[name]

    def list_agents(self):

        return list(
            self._agents.keys()
        )


registry = AgentRegistry()