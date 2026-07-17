from __future__ import annotations

import shutil
from pathlib import Path

from applications.platform.platform_result import EnterpriseWorkspace
from applications.platform.platform_store import PlatformStore
from applications.platform.settings import PlatformSettings


class EnterpriseWorkspaceManager:
    """
    企业级多 Workspace 管理。

    区别于 software_team.project.workspace.WorkspaceManager（单项目目录）。
    """

    STORE_KEY = "workspaces"

    def __init__(
        self,
        settings: PlatformSettings | None = None,
        store: PlatformStore | None = None,
    ):

        self._settings = settings or PlatformSettings()
        self._store = store or PlatformStore(settings=self._settings)
        self._root = self._settings.workspace_root
        self._root.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        *,
        name: str,
        organization_id: str,
    ) -> EnterpriseWorkspace:

        slug = self._normalize(name)
        root_path = str(self._root / organization_id / slug)
        Path(root_path).mkdir(parents=True, exist_ok=True)

        workspace = EnterpriseWorkspace.create(
            name=name,
            organization_id=organization_id,
            root_path=root_path,
        )

        self._store.append(self.STORE_KEY, self._to_dict(workspace))

        return workspace

    def get(self, workspace_id: str) -> EnterpriseWorkspace | None:

        data = self._store.find(self.STORE_KEY, workspace_id)

        if data is None:

            return None

        return self._from_dict(data)

    def get_or_create_default(
        self,
        organization_id: str,
    ) -> EnterpriseWorkspace:

        items = self._store.filter(
            self.STORE_KEY,
            organization_id=organization_id,
        )

        if items:

            return self._from_dict(items[0])

        return self.create(
            name=self._settings.default_workspace_name,
            organization_id=organization_id,
        )

    def register_project(
        self,
        workspace_id: str,
        project_id: str,
    ) -> EnterpriseWorkspace | None:

        workspace = self.get(workspace_id)

        if workspace is None:

            return None

        if project_id not in workspace.project_ids:

            workspace.project_ids.append(project_id)
            self._store.replace(
                self.STORE_KEY,
                workspace_id,
                self._to_dict(workspace),
            )

        return workspace

    def list_by_organization(
        self,
        organization_id: str,
    ) -> list[EnterpriseWorkspace]:

        return [
            self._from_dict(item)
            for item in self._store.filter(
                self.STORE_KEY,
                organization_id=organization_id,
            )
        ]

    def remove(self, workspace_id: str) -> bool:

        workspace = self.get(workspace_id)

        if workspace is None:

            return False

        path = Path(workspace.root_path)

        if path.is_dir():

            shutil.rmtree(path, ignore_errors=True)

        items = [
            item
            for item in self._store.load(self.STORE_KEY)
            if item.get("id") != workspace_id
        ]
        self._store.save(self.STORE_KEY, items)

        return True

    @staticmethod
    def summarize(workspace: EnterpriseWorkspace) -> str:

        return (
            f"{workspace.name} (id={workspace.id})\n"
            f"Organization: {workspace.organization_id}\n"
            f"Root: {workspace.root_path}\n"
            f"Projects: {len(workspace.project_ids)}"
        )

    @staticmethod
    def _normalize(name: str) -> str:

        return name.strip().lower().replace(" ", "_")

    @staticmethod
    def _to_dict(workspace: EnterpriseWorkspace) -> dict:

        return {
            "id": workspace.id,
            "name": workspace.name,
            "organization_id": workspace.organization_id,
            "root_path": workspace.root_path,
            "project_ids": workspace.project_ids,
            "metadata": workspace.metadata,
        }

    @staticmethod
    def _from_dict(data: dict) -> EnterpriseWorkspace:

        return EnterpriseWorkspace(
            id=data["id"],
            name=data["name"],
            organization_id=data["organization_id"],
            root_path=data["root_path"],
            project_ids=data.get("project_ids", []),
            metadata=data.get("metadata", {}),
        )
