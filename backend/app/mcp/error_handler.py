from app.core.logger import logger
from app.mcp.exceptions import MCPConnectionError
from app.mcp.exceptions import MCPError
from app.mcp.exceptions import MCPNetworkError
from app.mcp.exceptions import MCPNotConnectedError
from app.mcp.exceptions import MCPPromptNotFoundError
from app.mcp.exceptions import MCPResourceNotFoundError
from app.mcp.exceptions import MCPTimeoutError
from app.mcp.exceptions import MCPToolNotFoundError
from app.tools.types import ToolResult


class MCPErrorHandler:
    """
    统一处理 MCP 相关异常。

    避免在业务代码中散落 try/except。
    后续可扩展 OAuth、Streaming、Health Check 等错误类型。
    """

    def handle_connection_error(
        self,
        error: Exception,
        server_name: str,
    ) -> None:

        logger.error(
            "MCP server '%s' connection error: %s",
            server_name,
            error,
        )

        if isinstance(error, MCPConnectionError):

            raise error

        raise MCPConnectionError(
            f"Failed to connect MCP server '{server_name}': {error}"
        ) from error

    def handle_tool_not_found(
        self,
        tool_name: str,
        server_name: str,
    ) -> ToolResult:

        message = (
            f"MCP tool '{tool_name}' not found on "
            f"server '{server_name}'."
        )

        logger.error(message)

        return ToolResult(
            success=False,
            content=message,
        )

    def handle_resource_not_found(
        self,
        resource_id: str,
        server_name: str,
    ) -> str:

        message = (
            f"MCP resource '{resource_id}' not found on "
            f"server '{server_name}'."
        )

        logger.error(message)

        return message

    def handle_prompt_not_found(
        self,
        prompt_name: str,
        server_name: str,
    ) -> None:

        message = (
            f"MCP prompt '{prompt_name}' not found on "
            f"server '{server_name}'."
        )

        logger.error(message)

        raise MCPPromptNotFoundError(message)

    def handle_timeout(
        self,
        error: Exception,
        server_name: str,
    ) -> ToolResult:

        logger.error(
            "MCP server '%s' timeout: %s",
            server_name,
            error,
        )

        return ToolResult(
            success=False,
            content=f"MCP request timed out on '{server_name}': {error}",
        )

    def handle_network_error(
        self,
        error: Exception,
        server_name: str,
    ) -> ToolResult:

        logger.error(
            "MCP server '%s' network error: %s",
            server_name,
            error,
        )

        if isinstance(error, MCPNetworkError):

            message = str(error)

        else:

            message = (
                f"MCP network error on '{server_name}': {error}"
            )

        return ToolResult(
            success=False,
            content=message,
        )

    def handle_tool_call_error(
        self,
        error: Exception,
        tool_name: str,
        server_name: str,
    ) -> ToolResult:

        if isinstance(error, MCPTimeoutError):

            return self.handle_timeout(
                error,
                server_name,
            )

        if isinstance(error, MCPNetworkError):

            return self.handle_network_error(
                error,
                server_name,
            )

        if isinstance(error, MCPToolNotFoundError):

            return self.handle_tool_not_found(
                tool_name,
                server_name,
            )

        if isinstance(error, MCPNotConnectedError):

            return ToolResult(
                success=False,
                content=str(error),
            )

        logger.error(
            "MCP tool '%s' on '%s' failed: %s",
            tool_name,
            server_name,
            error,
        )

        return ToolResult(
            success=False,
            content=f"MCP tool error: {error}",
        )

    def safe_call(
        self,
        server_name: str,
        operation: str,
        callback,
    ):
        """
        包装 MCP Client 调用，统一捕获异常。
        """

        try:

            return callback()

        except MCPError:

            raise

        except TimeoutError as error:

            raise MCPTimeoutError(
                f"MCP {operation} timed out on "
                f"'{server_name}': {error}"
            ) from error

        except OSError as error:

            raise MCPNetworkError(
                f"MCP {operation} network error on "
                f"'{server_name}': {error}"
            ) from error

        except Exception as error:

            raise MCPError(
                f"MCP {operation} failed on "
                f"'{server_name}': {error}"
            ) from error
