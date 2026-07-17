from __future__ import annotations

from applications.platform.platform_result import RegisteredProject
from applications.platform.platform_result import TeamType
from applications.platform.platform_store import PlatformStore
from applications.platform.settings import PlatformSettings


class ProjectRegistry:
    """
    统一管理所有 Project。
    """

    STORE_KEY = "projects"

    def __init__(
        self,
        settings: PlatformSettings | None = None,
        store: PlatformStore | None = None,
    ):

        self._settings = settings or PlatformSettings()
        self._store = store or PlatformStore(settings=self._settings)

    def register(
        self,
        *,
        name: str,
        organization_id: str,
        workspace_id: str,
        team_type: TeamType = TeamType.SOFTWARE,
        requirement: str = "",
        owner_id: str = "",
        workspace_path: str = "",
    ) -> RegisteredProject:

        project = RegisteredProject.create(
            name=name,
            organization_id=organization_id,
            workspace_id=workspace_id,
            team_type=team_type,
            requirement=requirement,
            owner_id=owner_id,
            workspace_path=workspace_path,
        )

        self._store.append(self.STORE_KEY, self._to_dict(project))

        return project

    def get(self, project_id: str) -> RegisteredProject | None:

        data = self._store.find(self.STORE_KEY, project_id)

        if data is None:

            return None

        return self._from_dict(data)

    def update_status(
        self,
        project_id: str,
        status: str,
    ) -> RegisteredProject | None:

        project = self.get(project_id)

        if project is None:

            return None

        project.status = status
        self._store.replace(
            self.STORE_KEY,
            project_id,
            self._to_dict(project),
        )

        return project

    def update_workspace_path(
        self,
        project_id: str,
        workspace_path: str,
    ) -> RegisteredProject | None:

        project = self.get(project_id)

        if project is None:

            return None

        project.workspace_path = workspace_path
        self._store.replace(
            self.STORE_KEY,
            project_id,
            self._to_dict(project),
        )

        return project

    def list_by_workspace(
        self,
        workspace_id: str,
    ) -> list[RegisteredProject]:

        return [
            self._from_dict(item)
            for item in self._store.filter(
                self.STORE_KEY,
                workspace_id=workspace_id,
            )
        ]

    def list_by_organization(
        self,
        organization_id: str,
    ) -> list[RegisteredProject]:

        return [
            self._from_dict(item)
            for item in self._store.filter(
                self.STORE_KEY,
                organization_id=organization_id,
            )
        ]

    def list_all(self) -> list[RegisteredProject]:

        return [
            self._from_dict(item)
            for item in self._store.load(self.STORE_KEY)
        ]

    @staticmethod
    def summarize(project: RegisteredProject) -> str:

        return (
            f"{project.name} (id={project.id}, status={project.status})\n"
            f"Team: {project.team_type.value}\n"
            f"Workspace: {project.workspace_id}\n"
            f"Path: {project.workspace_path or 'n/a'}"
        )

    @staticmethod
    def _to_dict(project: RegisteredProject) -> dict:

        return {
            "id": project.id,
            "name": project.name,
            "organization_id": project.organization_id,
            "workspace_id": project.workspace_id,
            "team_type": project.team_type.value,
            "requirement": project.requirement,
            "status": project.status,
            "owner_id": project.owner_id,
            "workspace_path": project.workspace_path,
            "metadata": project.metadata,
        }

    @staticmethod
    def _from_dict(data: dict) -> RegisteredProject:

        return RegisteredProject(
            id=data["id"],
            name=data["name"],
            organization_id=data["organization_id"],
            workspace_id=data["workspace_id"],
            team_type=TeamType(data["team_type"]),
            requirement=data.get("requirement", ""),
            status=data.get("status", "created"),
            owner_id=data.get("owner_id", ""),
            workspace_path=data.get("workspace_path", ""),
            metadata=data.get("metadata", {}),
        )
