from applications.software_team.management.management_result import DeliveryEvaluation
from applications.software_team.management.management_result import ManagementContext
from applications.software_team.management.management_result import ManagementEventType
from applications.software_team.management.management_result import ManagementPipelineResult
from applications.software_team.management.management_result import Milestone
from applications.software_team.management.management_result import MilestoneResult
from applications.software_team.management.management_result import MilestoneStatus
from applications.software_team.management.management_result import PlanPhase
from applications.software_team.management.management_result import PlanningResult
from applications.software_team.management.management_result import ProgressSnapshot
from applications.software_team.management.management_result import ProjectPlan
from applications.software_team.management.management_result import Risk
from applications.software_team.management.management_result import RiskAssessmentResult
from applications.software_team.management.management_result import RiskLevel
from applications.software_team.management.management_result import RiskStatus
from applications.software_team.management.management_result import TaskBreakdownResult
from applications.software_team.management.management_result import TaskItem
from applications.software_team.management.management_result import TaskPriority
from applications.software_team.management.management_result import TaskStatus
from applications.software_team.management.management_result import WorkloadSnapshot

__all__ = [
    "DeliveryEvaluation",
    "ManagementContext",
    "ManagementEventType",
    "ManagementPipelineResult",
    "ManagementService",
    "Milestone",
    "MilestoneManager",
    "MilestoneResult",
    "MilestoneStatus",
    "PlanPhase",
    "PlanningManager",
    "PlanningResult",
    "ProgressManager",
    "ProgressSnapshot",
    "ProjectManager",
    "ProjectPlan",
    "Risk",
    "RiskAssessmentResult",
    "RiskLevel",
    "RiskManager",
    "RiskStatus",
    "TaskBreakdownResult",
    "TaskItem",
    "TaskManager",
    "TaskPriority",
    "TaskStatus",
    "WorkloadManager",
    "WorkloadSnapshot",
]


def __getattr__(name: str):

    if name == "ManagementService":
        from applications.software_team.management.management_service import (
            ManagementService,
        )

        return ManagementService

    if name == "MilestoneManager":
        from applications.software_team.management.milestone_manager import (
            MilestoneManager,
        )

        return MilestoneManager

    if name == "PlanningManager":
        from applications.software_team.management.planning_manager import (
            PlanningManager,
        )

        return PlanningManager

    if name == "ProgressManager":
        from applications.software_team.management.progress_manager import (
            ProgressManager,
        )

        return ProgressManager

    if name == "ProjectManager":
        from applications.software_team.management.project_manager import (
            ProjectManager,
        )

        return ProjectManager

    if name == "RiskManager":
        from applications.software_team.management.risk_manager import RiskManager

        return RiskManager

    if name == "TaskManager":
        from applications.software_team.management.task_manager import TaskManager

        return TaskManager

    if name == "WorkloadManager":
        from applications.software_team.management.workload_manager import (
            WorkloadManager,
        )

        return WorkloadManager

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
