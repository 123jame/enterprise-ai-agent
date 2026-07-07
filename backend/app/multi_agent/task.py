from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DELEGATED = "delegated"


def _new_task_id() -> str:
    return uuid4().hex[:12]


@dataclass
class Task:
    """
    Multi-Agent 任务单元，支持拆分。
    """

    goal: str

    input: str

    id: str = field(
        default_factory=_new_task_id
    )

    output: str = ""

    status: TaskStatus = TaskStatus.PENDING

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    subtasks: list["Task"] = field(
        default_factory=list
    )

    assigned_agent: str = ""
