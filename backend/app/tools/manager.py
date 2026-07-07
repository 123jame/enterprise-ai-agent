from app.tools.factory import ToolFactory
from app.tools.registry import ToolRegistry
from app.tools.types import ToolContext
from app.tools.types import ToolResult

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.mcp.server_manager import MCPServerManager
    from app.runtime.config import AgentConfig
    from app.runtime.tracer import AgentTracer


class ToolManager:
    """
    Tool 管理器。

    统一管理本地 Tool 与 MCP Tool，对 ChatAgent 暴露统一接口。
    """

    def __init__(
        self,
        config: "AgentConfig | None" = None,
        mcp_server_manager: "MCPServerManager | None" = None,
        tracer: "AgentTracer | None" = None,
    ):

        from app.runtime.config import AgentConfig

        self._config = config or AgentConfig()
        self._mcp_server_manager = mcp_server_manager
        self._tracer = tracer
        self._mcp_tools: dict[str, object] = {}

        if (
            self._config.enable_mcp
            and self._mcp_server_manager is not None
            and self._config.auto_discover_tools
        ):

            self.refresh_mcp_tools()

    def bind_mcp(
        self,
        server_manager: "MCPServerManager",
    ) -> None:

        self._mcp_server_manager = server_manager

        if (
            self._config.enable_mcp
            and self._config.auto_discover_tools
        ):

            self.refresh_mcp_tools()

    def refresh_mcp_tools(self) -> None:

        if self._mcp_server_manager is None:

            return

        self._mcp_tools = {
            tool.name: tool
            for tool in self._mcp_server_manager.discover_tools()
        }

    def get_schemas(self) -> list[dict]:

        schemas = ToolRegistry.get_schemas()

        schemas.extend(
            tool.schema
            for tool in self._mcp_tools.values()
        )

        return schemas

    @classmethod
    def execute(
        cls,
        context: ToolContext,
    ) -> ToolResult:

        return cls().execute_instance(context)

    def execute_instance(
        self,
        context: ToolContext,
    ) -> ToolResult:

        if context.tool_name in self._mcp_tools:

            tool = self._mcp_tools[context.tool_name]

            if self._tracer is not None:

                server_name = getattr(
                    tool,
                    "server_name",
                    "unknown",
                )

                mcp_tool_name = getattr(
                    tool,
                    "mcp_tool_name",
                    context.tool_name,
                )

                self._tracer.on_mcp_tool_call(
                    server_name=server_name,
                    tool_name=mcp_tool_name,
                    arguments=context.arguments,
                )

            return tool.execute(context)

        tool = ToolFactory.get(
            context.tool_name
        )

        return tool.execute(
            context
        )

    def execute(
        self,
        context: ToolContext,
    ) -> ToolResult:

        return self.execute_instance(context)
