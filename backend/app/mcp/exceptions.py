class MCPError(Exception):
    """
    MCP 基础异常。
    """

    pass


class MCPConnectionError(MCPError):
    """
    MCP Server 连接失败或不可用。
    """

    pass


class MCPNotConnectedError(MCPError):
    """
    在未连接状态下调用 MCP 操作。
    """

    pass


class MCPToolNotFoundError(MCPError):
    """
    MCP Tool 不存在。
    """

    pass


class MCPResourceNotFoundError(MCPError):
    """
    MCP Resource 不存在。
    """

    pass


class MCPPromptNotFoundError(MCPError):
    """
    MCP Prompt 不存在。
    """

    pass


class MCPTimeoutError(MCPError):
    """
    MCP 请求超时。
    """

    pass


class MCPNetworkError(MCPError):
    """
    MCP 网络异常。
    """

    pass
