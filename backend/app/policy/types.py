from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any


class PolicyProviderType(str, Enum):
    """
    策略模型提供方类型。

    当前仅实现 MOCK；其余类型预留，便于后续接入真实 VLA 模型。
    """

    MOCK = "mock"

    # 预留扩展：OpenVLA / RT-2 / π0
    OPENVLA = "openvla"
    RT2 = "rt2"
    PI0 = "pi0"


@dataclass
class PolicyAction:
    """
    策略模型建议的单步动作。
    """

    name: str

    parameters: dict[str, Any] = field(
        default_factory=dict,
    )

    description: str = ""


@dataclass
class PolicyPrediction:
    """
    策略模型预测结果。

    actions 可直接映射为 Tool Calling 参数，供 Agent 或 Demo 使用。
    """

    provider: str

    instruction: str

    observation_type: str

    actions: list[PolicyAction]

    reasoning: str

    confidence: float = 0.0

    completed: bool = False

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典，便于日志与序列化。"""

        return {
            "provider": self.provider,
            "instruction": self.instruction,
            "observation_type": self.observation_type,
            "actions": [
                {
                    "name": action.name,
                    "parameters": action.parameters,
                    "description": action.description,
                }
                for action in self.actions
            ],
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "completed": self.completed,
            "metadata": self.metadata,
        }
