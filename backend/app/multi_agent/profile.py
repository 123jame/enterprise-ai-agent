from dataclasses import dataclass
from dataclasses import field


@dataclass
class AgentProfile:
    """
    Agent 描述信息，供 Registry 与 Router 使用。
    """

    name: str

    role: str

    description: str

    capabilities: list[str] = field(
        default_factory=list
    )

    supported_tools: list[str] = field(
        default_factory=list
    )

    supported_resources: list[str] = field(
        default_factory=list
    )

    keywords: list[str] = field(
        default_factory=list
    )
