from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryRecord:
    """
    Memory中的一条记录
    """

    role: str

    content: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class MemoryContext:
    """
    一次Memory查询返回的数据
    """

    session_id: str

    records: list[MemoryRecord] = field(
        default_factory=list
    )