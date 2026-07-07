from app.agents.registry import registry


class AgentFactory:

    @staticmethod
    def create(
        name: str
    ):

        agent_cls = registry.get(name)

        return agent_cls()

    @staticmethod
    def get(
        name: str
    ):
        """
        向后兼容别名。
        """

        return AgentFactory.create(name)