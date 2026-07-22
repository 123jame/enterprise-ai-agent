from app.embodied.types import Observation
from app.llm.types import Message
from app.llm.types import ToolCall
from app.tools.types import ToolResult


class EmbodiedAgentLoopHelper:
    """
    具身智能 Agent Loop 辅助器。

    负责将 Tool Action 结果转换为 Observation，并构建 Tool Message。

    循环模型：
        LLM Reasoning -> Tool Action -> Environment -> Observation -> Reasoning
    """

    def __init__(
        self,
        observation_builder,
    ) -> None:

        self._observation_builder = observation_builder

    def collect_observations(
        self,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
    ) -> list[Observation]:
        """从一轮 Tool 执行中收集 Observation 列表。"""

        observations: list[Observation] = []

        for tool_call, tool_result in zip(
            tool_calls,
            tool_results,
            strict=True,
        ):

            observation = self._observation_builder.build_observation(
                tool_result,
                tool_name=tool_call.name,
            )

            observations.append(observation)

        return observations

    def build_tool_round(
        self,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        *,
        assistant_content: str | None = None,
        tool_message_builder,
    ) -> list[Message]:
        """
        构建一轮 Tool Calling Message。

        复用 ToolMessageBuilder，确保与现有 Tool Calling 协议兼容。
        """

        return tool_message_builder.build_tool_round(
            tool_calls,
            tool_results,
            assistant_content=assistant_content,
        )
