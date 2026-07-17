from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class DashboardEventType(str, Enum):
    """
    Dashboard WebSocket 事件类型。
    """

    PROJECT_STARTED = "project_started"
    PROJECT_FINISHED = "project_finished"
    TASK_FINISHED = "task_finished"
    AGENT_STARTED = "agent_started"
    AGENT_FINISHED = "agent_finished"
    WORKFLOW_STATUS = "workflow_status"
    DEPLOYMENT_FINISHED = "deployment_finished"
    RELEASE_FINISHED = "release_finished"
    OPERATION_UPDATE = "operation_update"
    GIT_UPDATE = "git_update"
    KNOWLEDGE_UPDATE = "knowledge_update"
    LOG = "log"


class DashboardEvent(BaseModel):
    """
    统一 Dashboard 事件载荷。
    """

    type: DashboardEventType
    project_id: str = ""
    session_id: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = ""


WORKFLOW_STAGES: tuple[str, ...] = (
    "requirement",
    "planning",
    "architecture",
    "development",
    "verification",
    "git",
    "deployment",
    "operations",
    "knowledge",
    "completed",
)

AGENT_STAGE_MAP: dict[str, str] = {
    "ProductAgent": "planning",
    "ArchitectAgent": "architecture",
    "BackendAgent": "development",
    "FrontendAgent": "development",
    "QAAgent": "verification",
    "DocumentationAgent": "deployment",
}
