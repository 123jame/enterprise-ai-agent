from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class ManagementEventType(str, Enum):
    """
    Memory 项目管理事件类型。
    """

    PROJECT = "project_history"
    TASK = "task_history"
    MILESTONE = "milestone_history"
    RISK = "risk_history"
    PROGRESS = "project_history"
    DELIVERY = "project_history"


class TaskStatus(str, Enum):
    """
    任务状态。
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """
    任务优先级。
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MilestoneStatus(str, Enum):
    """
    里程碑状态。
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"


class RiskLevel(str, Enum):
    """
    风险等级。
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskStatus(str, Enum):
    """
    风险状态。
    """

    OPEN = "open"
    MITIGATED = "mitigated"
    CLOSED = "closed"


@dataclass
class PlanPhase:
    """
    项目计划阶段。
    """

    name: str
    agent_name: str
    duration_days: int
    description: str = ""
    order: int = 0


@dataclass
class ProjectPlan:
    """
    项目计划。
    """

    project_id: str
    project_name: str
    phases: list[PlanPhase] = field(default_factory=list)
    total_duration_days: int = 0
    resources: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
    )
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskItem:
    """
    项目任务项。
    """

    id: str
    title: str
    assignee: str
    status: TaskStatus
    priority: TaskPriority
    phase: str = ""
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        title: str,
        assignee: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        phase: str = "",
        description: str = "",
        dependencies: list[str] | None = None,
        status: TaskStatus = TaskStatus.PENDING,
    ) -> TaskItem:

        return cls(
            id=f"task_{uuid4().hex[:12]}",
            title=title,
            assignee=assignee,
            status=status,
            priority=priority,
            phase=phase,
            description=description,
            dependencies=dependencies or [],
        )


@dataclass
class Milestone:
    """
    项目里程碑。
    """

    id: str
    name: str
    status: MilestoneStatus
    phase: str = ""
    description: str = ""
    target_date: str = ""
    task_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        name: str,
        phase: str = "",
        description: str = "",
        target_date: str = "",
        task_ids: list[str] | None = None,
        status: MilestoneStatus = MilestoneStatus.PENDING,
    ) -> Milestone:

        return cls(
            id=f"milestone_{uuid4().hex[:12]}",
            name=name,
            status=status,
            phase=phase,
            description=description,
            target_date=target_date,
            task_ids=task_ids or [],
        )


@dataclass
class Risk:
    """
    项目风险项。
    """

    id: str
    title: str
    level: RiskLevel
    status: RiskStatus
    category: str = ""
    description: str = ""
    mitigation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        title: str,
        level: RiskLevel,
        category: str = "",
        description: str = "",
        mitigation: str = "",
        status: RiskStatus = RiskStatus.OPEN,
    ) -> Risk:

        return cls(
            id=f"risk_{uuid4().hex[:12]}",
            title=title,
            level=level,
            status=status,
            category=category,
            description=description,
            mitigation=mitigation,
        )


@dataclass
class PlanningResult:
    """
    规划结果。
    """

    success: bool
    plan: ProjectPlan | None = None
    plan_path: str = ""
    error_message: str = ""


@dataclass
class TaskBreakdownResult:
    """
    任务拆分结果。
    """

    success: bool
    tasks: list[TaskItem] = field(default_factory=list)
    task_list_path: str = ""
    error_message: str = ""


@dataclass
class MilestoneResult:
    """
    里程碑管理结果。
    """

    success: bool
    milestones: list[Milestone] = field(default_factory=list)
    milestone_report_path: str = ""
    current_milestone: Milestone | None = None
    error_message: str = ""


@dataclass
class RiskAssessmentResult:
    """
    风险评估结果。
    """

    success: bool
    risks: list[Risk] = field(default_factory=list)
    risk_report_path: str = ""
    summary: str = ""
    error_message: str = ""


@dataclass
class ProgressSnapshot:
    """
    进度快照。
    """

    completion_rate: float
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    remaining_tasks: int
    agent_status: dict[str, str] = field(default_factory=dict)
    progress_report_path: str = ""

    @property
    def summary(self) -> str:

        return (
            f"Progress: {self.completion_rate:.0%} "
            f"({self.completed_tasks}/{self.total_tasks} tasks)"
        )


@dataclass
class WorkloadSnapshot:
    """
    Agent 工作负载快照。
    """

    loads: dict[str, int] = field(default_factory=dict)
    overloaded_agents: list[str] = field(default_factory=list)
    balanced: bool = True

    @property
    def summary(self) -> str:

        if not self.loads:

            return "Workload: no assignments"

        parts = [f"{agent}={count}" for agent, count in sorted(self.loads.items())]

        suffix = (
            f"; overloaded: {', '.join(self.overloaded_agents)}"
            if self.overloaded_agents
            else ""
        )

        return f"Workload: {', '.join(parts)}{suffix}"


@dataclass
class DeliveryEvaluation:
    """
    交付评估结果。
    """

    success: bool
    score: float
    criteria: dict[str, bool] = field(default_factory=dict)
    summary: str = ""
    error_message: str = ""


@dataclass
class ManagementContext:
    """
    项目管理上下文，供 PromptBuilder 注入。
    """

    project_summary: str = ""
    current_milestone: str = ""
    current_sprint: str = ""
    task_status_summary: str = ""
    risk_summary: str = ""
    progress_summary: str = ""
    workload_summary: str = ""

    def to_shared_context(self) -> dict[str, str]:

        return {
            "mgmt_project_summary": self.project_summary,
            "mgmt_current_milestone": self.current_milestone,
            "mgmt_current_sprint": self.current_sprint,
            "mgmt_task_status": self.task_status_summary,
            "mgmt_risk_summary": self.risk_summary,
            "mgmt_progress_summary": self.progress_summary,
            "mgmt_workload_summary": self.workload_summary,
        }

    def to_prompt_block(self) -> str:

        management_docs = "\n".join(
            f"- {path}"
            for path in (
                "management/PROJECT_PLAN.md",
                "management/TASK_LIST.md",
                "management/MILESTONE_REPORT.md",
                "management/PROGRESS_REPORT.md",
                "management/RISK_REPORT.md",
            )
        )

        return (
            f"## Project\n{self.project_summary or 'n/a'}\n\n"
            f"## Current Milestone\n{self.current_milestone or 'n/a'}\n\n"
            f"## Current Sprint\n{self.current_sprint or 'n/a'}\n\n"
            f"## Task Status\n{self.task_status_summary or 'n/a'}\n\n"
            f"## Risk Summary\n{self.risk_summary or 'none'}\n\n"
            f"## Progress\n{self.progress_summary or 'n/a'}\n\n"
            f"## Workload\n{self.workload_summary or 'n/a'}\n\n"
            f"## Management Documents\n"
            f"Use read_file with these paths:\n{management_docs}"
        )


@dataclass
class ProjectManagementState:
    """
    单个项目的管理运行时状态。
    """

    project_id: str
    plan: ProjectPlan | None = None
    tasks: list[TaskItem] = field(default_factory=list)
    milestones: list[Milestone] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    current_sprint: str = "Sprint 1"
    completed_agents: list[str] = field(default_factory=list)


@dataclass
class ManagementPipelineResult:
    """
    完整项目管理流水线结果。
    """

    success: bool
    planning: PlanningResult | None = None
    tasks: TaskBreakdownResult | None = None
    milestones: MilestoneResult | None = None
    risks: RiskAssessmentResult | None = None
    progress: ProgressSnapshot | None = None
    workload: WorkloadSnapshot | None = None
    delivery: DeliveryEvaluation | None = None
    context: ManagementContext = field(default_factory=ManagementContext)
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
