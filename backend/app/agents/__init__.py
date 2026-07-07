from app.agents.base_agent import BaseAgent
from app.agents.chat_agent import ChatAgent

from app.agents.registry import registry
from app.agents.factory import AgentFactory


registry.register(
    "chat",
    ChatAgent
)

__all__ = [

    "BaseAgent",

    "ChatAgent",

    "AgentFactory",

    "registry"

]