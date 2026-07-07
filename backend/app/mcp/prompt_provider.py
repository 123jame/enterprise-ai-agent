from abc import ABC
from abc import abstractmethod
from typing import Any

from app.mcp.types import MCPPromptDefinition
from app.mcp.types import MCPPromptResult


class MCPPromptProvider(ABC):
    """
    MCP Prompt 提供抽象。

    PromptBuilder 可选择是否引用 MCP Prompt。
    后续可扩展 Remote Server、Streaming Prompt 等。
    """

    @abstractmethod
    def list_prompts(self) -> list[MCPPromptDefinition]:
        pass

    @abstractmethod
    def get_prompt(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> MCPPromptResult:
        pass
