from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from typing import Any

from app.mcp.types import MCPResourceContent


@dataclass
class MCPResource:
    """
    统一的 MCP Resource 描述。
    """

    id: str

    name: str

    description: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    server_name: str = ""

    uri: str = ""


class MCPResourceProvider(ABC):
    """
    MCP Resource 读取抽象。

    后续可扩展 Multi KB、GraphRAG、Web Search 等。
    """

    @abstractmethod
    def list_resources(self) -> list[MCPResource]:
        pass

    @abstractmethod
    def read_resource(
        self,
        resource_id: str,
    ) -> MCPResourceContent:
        pass
