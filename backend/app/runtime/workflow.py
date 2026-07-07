"""
向后兼容导出。

旧版 dataclass Workflow 已替换为 Plan-and-Execute Workflow 抽象。
"""

from app.runtime.plan.workflow import SequentialWorkflow
from app.runtime.plan.workflow_base import Workflow

# 兼容旧名称
Step = None  # deprecated placeholder

__all__ = [
    "Workflow",
    "SequentialWorkflow",
]
