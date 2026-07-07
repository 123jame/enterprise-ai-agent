from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

from app.memory.types import MemoryRecord

if TYPE_CHECKING:
    from app.runtime.plan.types import Plan
    from app.runtime.plan.types import PlanStep


@dataclass
class AgentContext:
    """
    Agent 执行上下文
    """

    session_id: str

    user_message: str

    history: list[MemoryRecord] = field(
        default_factory=list
    )

    plan: "Plan | None" = None

    current_step: "PlanStep | None" = None


@dataclass
class AgentResult:
    """
    Agent 返回结果
    """

    success: bool

    model: str

    content: str
