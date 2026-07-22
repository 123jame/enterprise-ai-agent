from dataclasses import dataclass
from dataclasses import field
from typing import Any

from app.embodied.types import Observation
from app.policy.types import PolicyPrediction


@dataclass
class EmbodiedDemoStep:
    """
    Demo 执行步骤记录。
    """

    phase: str

    description: str

    tool_name: str | None = None

    tool_arguments: dict[str, Any] = field(
        default_factory=dict,
    )

    observation: Observation | None = None

    policy_prediction: PolicyPrediction | None = None

    success: bool = True

    detail: str = ""


@dataclass
class EmbodiedDemoResult:
    """
    具身智能 Demo 执行结果。
    """

    instruction: str

    success: bool

    content: str

    steps: list[EmbodiedDemoStep] = field(
        default_factory=list,
    )

    observations: list[Observation] = field(
        default_factory=list,
    )

    final_robot_state: dict[str, Any] = field(
        default_factory=dict,
    )
