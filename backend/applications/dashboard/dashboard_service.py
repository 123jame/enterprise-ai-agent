from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.memory.manager import MemoryManager

from applications.dashboard.event_types import WORKFLOW_STAGES
from applications.dashboard.state_store import get_state_store
from applications.dashboard.state_store import ProjectRuntimeState
from applications.platform.governance_manager import GovernanceManager
from applications.platform.settings import PlatformSettings
from applications.software_team.config.settings import SoftwareTeamSettings


class DashboardService:
    """
    Dashboard 只读数据聚合服务。

    所有业务逻辑仍由 Backend Manager / Coordinator 完成，
    本类仅聚合展示数据。
    """

    def __init__(
        self,
        platform_settings: PlatformSettings | None = None,
        team_settings: SoftwareTeamSettings | None = None,
    ):

        self._platform_settings = platform_settings or PlatformSettings()
        self._team_settings = team_settings or SoftwareTeamSettings()
        self._governance = GovernanceManager(settings=self._platform_settings)
        self._state = get_state_store()
        self._memory = MemoryManager()

    def list_projects(self) -> list[dict[str, Any]]:

        runtime = [
            self._serialize_runtime(item)
            for item in self._state.list_projects()
        ]
        registered = [
            self._serialize_registered(item)
            for item in self._governance.projects.list_all()
        ]

        merged: dict[str, dict[str, Any]] = {}

        for item in registered:

            merged[item["id"]] = item

        for item in runtime:

            merged[item["id"]] = {**merged.get(item["id"], {}), **item}

            session_id = item.get("session_id")

            if session_id:

                for reg in registered:

                    if (
                        reg["name"] == item.get("name")
                        and reg["requirement"] == item.get("requirement")
                        and reg["id"] != item["id"]
                    ):

                        merged[reg["id"]] = {
                            **merged.get(reg["id"], reg),
                            **item,
                            "id": reg["id"],
                        }

        return sorted(
            merged.values(),
            key=lambda item: item.get("started_at", item.get("created_at", "")),
            reverse=True,
        )

    def get_project(self, project_id: str) -> dict[str, Any] | None:

        runtime = self._resolve_runtime(project_id)
        registered = self._governance.projects.get(project_id)

        if runtime is None and registered is None:

            return None

        data: dict[str, Any] = {}

        if registered is not None:

            data = self._serialize_registered(registered)

        if runtime is not None:

            data.update(self._serialize_runtime(runtime))
            data["id"] = project_id

        return data

    def get_workflow(self, project_id: str) -> dict[str, Any]:

        runtime = self._resolve_runtime(project_id)

        if runtime is None:

            return {
                "project_id": project_id,
                "current_stage": "requirement",
                "stages": [],
            }

        return {
            "project_id": project_id,
            "current_stage": runtime.current_stage,
            "status": runtime.status,
            "stages": [asdict(stage) for stage in runtime.workflow_stages],
            "logs": runtime.logs[-50:],
        }

    def get_agents(self, project_id: str = "") -> list[dict[str, Any]]:

        default_agents = [
            "ProductAgent",
            "ArchitectAgent",
            "BackendAgent",
            "FrontendAgent",
            "QAAgent",
            "DocumentationAgent",
        ]

        if project_id:

            runtime = self._resolve_runtime(project_id)

            if runtime is None:

                return [
                    {"name": name, "status": "idle"}
                    for name in default_agents
                ]

            return [asdict(agent) for agent in runtime.agents.values()]

        agents: dict[str, dict[str, Any]] = {
            name: {
                "name": name,
                "status": "idle",
                "current_task": "",
                "token_usage": 0,
                "execution_time_ms": 0.0,
                "tool_calls": 0,
                "workload": 0.0,
            }
            for name in default_agents
        }

        for project in self._state.list_projects():

            for agent in project.agents.values():

                existing = agents.get(agent.name)

                if existing is None or agent.status == "running":

                    agents[agent.name] = asdict(agent)

        return list(agents.values())

    def get_project_detail(self, project_id: str) -> dict[str, Any]:

        project = self.get_project(project_id) or {"id": project_id}
        runtime = self._resolve_runtime(project_id)

        default_agents = [
            "ProductAgent",
            "ArchitectAgent",
            "BackendAgent",
            "FrontendAgent",
            "QAAgent",
            "DocumentationAgent",
        ]

        if runtime and runtime.agents:

            tasks = [
                {
                    "id": agent.name,
                    "title": agent.current_task or agent.name,
                    "assignee": agent.name,
                    "status": agent.status,
                    "priority": "high" if agent.status == "running" else "medium",
                }
                for agent in runtime.agents.values()
            ]

        else:

            tasks = [
                {
                    "id": name,
                    "title": name,
                    "assignee": name,
                    "status": "pending",
                    "priority": "medium",
                }
                for name in default_agents
            ]

        milestones = [
            {
                "id": stage.id,
                "name": stage.label,
                "status": stage.status,
            }
            for stage in (runtime.workflow_stages if runtime else _default_workflow_stages())
        ]

        progress = self._calculate_progress(project, runtime, tasks)

        risks = []

        if runtime and runtime.status == "failed":

            risks.append(
                {
                    "id": "pipeline-failure",
                    "title": "Pipeline execution failed",
                    "level": "high",
                    "status": "open",
                    "description": runtime.logs[-1] if runtime.logs else "",
                }
            )

        return {
            "project": project,
            "tasks": tasks,
            "milestones": milestones,
            "progress": progress,
            "risks": risks,
            "workflow": self.get_workflow(project_id),
            "agents": self.get_agents(project_id),
            "logs": runtime.logs[-100:] if runtime else [],
        }

    def get_git(self, project_id: str) -> dict[str, Any]:

        project = self.get_project(project_id) or {}
        workspace_path = project.get("workspace_path", "")
        runtime = self._state.get(project_id)

        branches: list[str] = []
        commits: list[dict[str, Any]] = []
        merges: list[dict[str, Any]] = []
        releases: list[dict[str, Any]] = []

        if runtime is not None:

            for entry in runtime.git_log:

                if entry.get("sha"):

                    commits.append(entry)

                if entry.get("merge"):

                    merges.append(entry)

        git_dir = Path(workspace_path) / ".git"

        if git_dir.is_dir():

            head = git_dir / "HEAD"

            if head.is_file():

                branches.append(head.read_text(encoding="utf-8").strip())

        deploy_log = runtime.deployment_log if runtime else {}

        if deploy_log.get("version"):

            releases.append(
                {
                    "version": deploy_log.get("version"),
                    "url": deploy_log.get("deploy_url", ""),
                }
            )

        return {
            "project_id": project_id,
            "branches": branches,
            "commits": commits,
            "merges": merges,
            "pull_requests": [],
            "releases": releases,
        }

    def get_deployment(self, project_id: str) -> dict[str, Any]:

        runtime = self._state.get(project_id)
        log = runtime.deployment_log if runtime else {}

        return {
            "project_id": project_id,
            "build": {
                "success": log.get("success"),
                "detail": log.get("error", ""),
            },
            "package": {"version": log.get("version", "")},
            "deploy": {"url": log.get("deploy_url", "")},
            "health_check": {"success": log.get("success")},
            "release": {
                "version": log.get("version", ""),
                "url": log.get("deploy_url", ""),
            },
        }

    def get_operations(self, project_id: str) -> dict[str, Any]:

        runtime = self._state.get(project_id)
        log = runtime.operations_log if runtime else {}

        return {
            "project_id": project_id,
            "cpu": log.get("cpu", {"value": 0, "unit": "%"}),
            "memory": log.get("memory", {"value": 0, "unit": "MB"}),
            "services": log.get("services", []),
            "health": log.get("health", {"status": "unknown"}),
            "alerts": log.get("alerts", []),
            "incidents": log.get("incidents", []),
        }

    def get_knowledge(self, project_id: str = "") -> dict[str, Any]:

        entries: list[dict[str, Any]] = []
        best_practices: list[str] = []
        lessons: list[str] = []
        history: list[dict[str, Any]] = []

        if project_id:

            project = self.get_project(project_id) or {}
            workspace_path = project.get("workspace_path", "")

            if workspace_path and Path(workspace_path).is_dir():

                knowledge_root = Path(workspace_path) / "knowledge"

                if knowledge_root.is_dir():

                    index_path = knowledge_root / "index.json"

                    if index_path.is_file():

                        entries.extend(
                            self._parse_knowledge_index(
                                index_path.read_text(encoding="utf-8"),
                            )
                        )

                    for path in knowledge_root.glob("*.json"):

                        if path.name in {"index.json", "catalog.json"}:

                            continue

                        try:
                            raw = json.loads(path.read_text(encoding="utf-8"))
                        except json.JSONDecodeError:
                            continue

                        entry = self._normalize_knowledge_entry(raw, path.stem)

                        if entry is not None:

                            entries.append(entry)

        return {
            "knowledge_base": entries,
            "best_practices": best_practices,
            "lessons_learned": lessons,
            "history": history,
        }

    def get_organization(self) -> dict[str, Any]:

        init = self._governance.initialize_platform()
        org_id = init.metadata.get("organization_id", "")
        workspace_id = init.metadata.get("workspace_id", "")

        workspaces = [
            {
                "id": item.id,
                "name": item.name,
                "organization_id": item.organization_id,
                "root_path": item.root_path,
            }
            for item in self._governance._workspace.list_by_organization(org_id)
        ]
        projects = [
            self._serialize_registered(item)
            for item in self._governance.projects.list_all()
        ]
        teams = [
            {
                "id": item.id,
                "name": item.name,
                "team_type": item.team_type.value,
            }
            for item in self._governance._teams.list_by_organization(org_id)
        ]

        return {
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "organization_summary": init.context.organization_summary,
            "workspaces": workspaces,
            "projects": projects,
            "teams": teams,
            "permissions": self._governance._permissions.summarize_permissions(
                subject_id="system",
            ),
        }

    def get_settings(self) -> dict[str, Any]:

        config = self._governance._config.load()

        return {
            "llm": config.get("llm", {}),
            "model": {
                "default_provider": self._platform_settings.default_model_provider,
                "default_model_id": self._platform_settings.default_model_id,
                "models": [
                    {
                        "id": model.id,
                        "name": model.name,
                        "provider": model.provider.value,
                    }
                    for model in self._governance._models.list_models()
                ],
            },
            "memory": config.get("memory", {}),
            "workflow": config.get("workflow", {}),
            "git": config.get("git", {}),
            "deployment": config.get("deployment", {}),
            "prompt": config.get("prompt", {}),
        }

    def get_memory(self, session_id: str) -> dict[str, Any]:

        context = self._memory.load(session_id)

        return {
            "session_id": session_id,
            "records": [
                {
                    "role": record.role,
                    "content": record.content[:2000],
                    "metadata": record.metadata,
                }
                for record in context.records
            ],
        }

    def get_prompt_debug(self, project_id: str) -> dict[str, Any]:

        runtime = self._state.get(project_id)

        return {
            "project_id": project_id,
            "prompt_blocks": [
                {
                    "agent": agent.name,
                    "status": agent.status,
                    "task": agent.current_task,
                }
                for agent in (runtime.agents.values() if runtime else [])
            ],
            "platform_context": (
                self._governance.build_context(project_id=project_id).to_shared_context()
            ),
        }

    def _resolve_runtime(
        self,
        project_id: str,
    ) -> ProjectRuntimeState | None:

        runtime = self._state.get(project_id)

        if runtime is not None:

            return runtime

        registered = self._governance.projects.get(project_id)

        if registered is None:

            return None

        for candidate in self._state.list_projects():

            if (
                candidate.name == registered.name
                and candidate.requirement == registered.requirement
            ):

                return candidate

        return None

    @staticmethod
    def _calculate_progress(
        project: dict[str, Any],
        runtime: ProjectRuntimeState | None,
        tasks: list[dict[str, Any]],
    ) -> dict[str, Any]:

        if runtime is not None and runtime.status == "finished":

            return {
                "summary": "Project completed",
                "completion_rate": 1.0,
                "completed_tasks": len(tasks),
                "total_tasks": len(tasks),
            }

        if runtime is not None and runtime.workflow_stages:

            stages = runtime.workflow_stages
            completed = sum(
                1 for stage in stages if stage.status == "completed"
            )
            total = len(stages)
            rate = completed / total if total else 0.0

            if runtime.status == "failed":

                rate = max(rate, completed / total if total else 0.0)

            return {
                "summary": f"{completed}/{total} workflow stages completed",
                "completion_rate": rate,
                "completed_tasks": completed,
                "total_tasks": total,
            }

        completed = sum(
            1 for task in tasks if task["status"] in {"completed", "success"}
        )
        total = max(len(tasks), 1)
        rate = completed / total

        status = project.get("status", "")

        if status == "finished":

            rate = 1.0
            completed = total

        elif status == "running" and rate == 0 and project.get("current_stage"):

            stage_order = list(WORKFLOW_STAGES)
            current = project.get("current_stage", "")

            if current in stage_order:

                rate = stage_order.index(current) / max(len(stage_order) - 1, 1)

        return {
            "summary": f"{completed}/{total} agents completed",
            "completion_rate": rate,
            "completed_tasks": completed,
            "total_tasks": total,
        }

    @staticmethod
    def _default_workflow_stages() -> list:

        labels = {
            "requirement": "Requirement",
            "planning": "Planning",
            "architecture": "Architecture",
            "development": "Development",
            "verification": "Verification",
            "git": "Git",
            "deployment": "Deployment",
            "operations": "Operations",
            "knowledge": "Knowledge",
            "completed": "Completed",
        }

        from applications.dashboard.state_store import WorkflowStageState

        return [
            WorkflowStageState(id=stage_id, label=labels[stage_id])
            for stage_id in WORKFLOW_STAGES
        ]

    @staticmethod
    def _parse_knowledge_index(raw_text: str) -> list[dict[str, Any]]:

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            return []

        if isinstance(data, list):

            return [
                item
                for item in (
                    DashboardService._normalize_knowledge_entry(entry, "")
                    for entry in data
                )
                if item is not None
            ]

        entry = DashboardService._normalize_knowledge_entry(data, "")

        return [entry] if entry is not None else []

    @staticmethod
    def _normalize_knowledge_entry(
        data: Any,
        fallback_id: str,
    ) -> dict[str, Any] | None:

        if not isinstance(data, dict):

            return None

        entry_id = (
            data.get("id")
            or data.get("entry_id")
            or fallback_id
        )

        title = data.get("title") or entry_id or fallback_id

        if not entry_id and not title:

            return None

        return {
            "id": entry_id,
            "title": title,
            "category": data.get("category", "general"),
            "source_path": data.get("source_path", ""),
        }

    @staticmethod
    def _serialize_registered(item) -> dict[str, Any]:

        return {
            "id": item.id,
            "name": item.name,
            "requirement": item.requirement,
            "status": item.status,
            "workspace_id": item.workspace_id,
            "workspace_path": item.workspace_path,
            "team_type": item.team_type.value,
            "owner_id": item.owner_id,
        }

    @staticmethod
    def _serialize_runtime(item) -> dict[str, Any]:

        return {
            "id": item.project_id,
            "session_id": item.session_id,
            "name": item.name,
            "requirement": item.requirement,
            "status": item.status,
            "current_stage": item.current_stage,
            "started_at": item.started_at,
            "finished_at": item.finished_at,
        }


_service: DashboardService | None = None


def get_dashboard_service() -> DashboardService:

    global _service

    if _service is None:

        _service = DashboardService()

    return _service
