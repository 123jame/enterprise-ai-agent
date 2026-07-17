from __future__ import annotations

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.management.management_result import TaskItem
from applications.software_team.management.management_result import TaskStatus
from applications.software_team.management.management_result import WorkloadSnapshot


class WorkloadManager:
    """
    统计各 Agent 工作负载，避免单个 Agent 长时间超负荷。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()

    def analyze(
        self,
        tasks: list[TaskItem],
    ) -> WorkloadSnapshot:

        loads: dict[str, int] = {}

        for task in tasks:

            if task.status in (
                TaskStatus.CANCELLED,
                TaskStatus.COMPLETED,
            ):

                continue

            loads[task.assignee] = loads.get(task.assignee, 0) + 1

        threshold = self._settings.management_task_overload_threshold

        overloaded = [
            agent
            for agent, count in loads.items()
            if count > threshold
        ]

        return WorkloadSnapshot(
            loads=loads,
            overloaded_agents=overloaded,
            balanced=len(overloaded) == 0,
        )

    def suggest_rebalance(
        self,
        snapshot: WorkloadSnapshot,
    ) -> list[str]:

        if snapshot.balanced:

            return []

        suggestions: list[str] = []

        for agent in snapshot.overloaded_agents:

            count = snapshot.loads.get(agent, 0)

            suggestions.append(
                f"Reduce pending tasks for {agent} (load={count})"
            )

        return suggestions
