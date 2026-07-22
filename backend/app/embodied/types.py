from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any


class ObservationType(str, Enum):
    """
    环境 Observation 类型。

    vision / robot 为具身智能反馈；tool 为普通 Tool；error 为失败反馈。
    """

    VISION = "vision"
    ROBOT = "robot"
    TOOL = "tool"
    ERROR = "error"
    GENERIC = "generic"


@dataclass
class Observation:
    """
    环境 Observation 对象。

    用于描述 Agent 执行 Action 后从环境获得的反馈，
    供后续 Reasoning 循环继续推理。
    """

    type: str

    content: str

    success: bool = True

    source: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典，便于序列化与日志记录。"""

        payload = {
            "type": self.type,
            "content": self.content,
            "success": self.success,
        }

        if self.source is not None:

            payload["source"] = self.source

        if self.metadata:

            payload["metadata"] = self.metadata

        return payload

    def to_json(self) -> str:
        """序列化为 JSON 字符串。"""

        import json

        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
        )

    def to_prompt_text(self) -> str:
        """
        转换为 LLM 可读的 Observation 文本。

        Task13.6 Agent Loop 可直接使用该格式注入上下文。
        """

        status = "success" if self.success else "error"

        prefix = f"[Observation:{self.type}:{status}]"

        if self.source:

            prefix = f"{prefix}[source={self.source}]"

        return f"{prefix} {self.content}"
