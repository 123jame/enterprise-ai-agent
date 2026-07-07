from abc import ABC
from abc import abstractmethod
from typing import Any

from app.mcp.types import MCPPromptDefinition
from app.mcp.types import MCPPromptResult
from app.mcp.types import MCPResourceContent
from app.mcp.types import MCPResourceInfo
from app.mcp.types import MCPToolCallResult
from app.mcp.types import MCPToolDefinition


class MCPClient(ABC):
    """
    MCP Client 抽象接口。

    单一职责：与 MCP Server 通信，暴露 Tool / Resource / Prompt 能力。
    不依赖任何具体 MCP SDK，后续可替换为 STDIO / HTTP / WebSocket 等实现。

    扩展预留：Remote MCP Server、OAuth、Streaming、Health Check。
    """

    @property
    @abstractmethod
    def server_name(self) -> str:
        """
        MCP Server 名称，用于多 Server 管理。
        """

        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """
        当前连接状态。
        """

        pass

    @abstractmethod
    def connect(self) -> None:
        """
        建立与 MCP Server 的连接。
        """

        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        断开与 MCP Server 的连接。
        """

        pass

    @abstractmethod
    def list_tools(self) -> list[MCPToolDefinition]:
        """
        列出 Server 暴露的全部 Tool。
        """

        pass

    @abstractmethod
    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> MCPToolCallResult:
        """
        调用 MCP Tool。
        """

        pass

    @abstractmethod
    def list_resources(self) -> list[MCPResourceInfo]:
        """
        列出 Server 暴露的全部 Resource。
        """

        pass

    @abstractmethod
    def read_resource(
        self,
        uri: str,
    ) -> MCPResourceContent:
        """
        读取指定 Resource 内容。
        """

        pass

    @abstractmethod
    def list_prompts(self) -> list[MCPPromptDefinition]:
        """
        列出 Server 暴露的全部 Prompt。
        """

        pass

    @abstractmethod
    def get_prompt(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> MCPPromptResult:
        """
        获取 MCP Prompt 渲染结果。
        """

        pass
