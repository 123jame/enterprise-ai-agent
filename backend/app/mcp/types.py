from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass
class MCPToolDefinition:
    """
    MCP Server 暴露的 Tool 定义。
    """

    name: str

    description: str

    input_schema: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class MCPToolCallResult:
    """
    MCP Tool 调用结果。
    """

    success: bool

    content: str

    is_error: bool = False


@dataclass
class MCPResourceInfo:
    """
    MCP Server 暴露的 Resource 元信息。
    """

    uri: str

    name: str

    description: str = ""

    mime_type: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class MCPResourceContent:
    """
    MCP Resource 读取结果。
    """

    uri: str

    content: str

    mime_type: str | None = None


@dataclass
class MCPPromptDefinition:
    """
    MCP Server 暴露的 Prompt 定义。
    """

    name: str

    description: str = ""

    arguments: list[dict[str, Any]] = field(
        default_factory=list
    )


@dataclass
class MCPPromptMessage:
    """
    MCP Prompt 中的一条消息。
    """

    role: str

    content: str


@dataclass
class MCPPromptResult:
    """
    MCP Prompt 获取结果。
    """

    name: str

    messages: list[MCPPromptMessage] = field(
        default_factory=list
    )

    description: str = ""
