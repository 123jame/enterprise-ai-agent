from typing import Any

from pydantic import BaseModel
from pydantic import Field


class ToolCall(BaseModel):
    """
    LLM 返回的单次 Tool Call。
    """

    id: str

    name: str

    arguments: dict[str, Any] = Field(
        default_factory=dict
    )


class Message(BaseModel):
    """
    LLM Message，兼容 OpenAI Tool Calling Protocol。
    """

    role: str

    content: str | None = ""

    tool_call_id: str | None = None

    name: str | None = None

    tool_calls: list[ToolCall] | None = None


class ChatResult(BaseModel):
    """
    LLM 返回结果。
    """

    model: str

    content: str | None = None

    tool_calls: list[ToolCall] = Field(
        default_factory=list
    )

    @property
    def tool_name(self) -> str | None:
        """
        向后兼容：返回第一个 Tool Call 名称。
        """

        if not self.tool_calls:

            return None

        return self.tool_calls[0].name

    @property
    def arguments(self) -> dict[str, Any]:
        """
        向后兼容：返回第一个 Tool Call 参数。
        """

        if not self.tool_calls:

            return {}

        return self.tool_calls[0].arguments

    @property
    def has_tool_calls(self) -> bool:

        return len(self.tool_calls) > 0
