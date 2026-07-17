from __future__ import annotations

import uuid
from typing import Optional

from applications.software_team.project.artifacts.artifact_manager import ArtifactManager
from applications.software_team.project.models.project import Project
from applications.software_team.project.models.project_status import ProjectStatus
from applications.software_team.project.workspace.workspace_manager import WorkspaceManager


class ProjectService:
    """
    项目生命周期管理。

    负责：

    - 创建 Project
    - 更新状态
    - 删除 Project
    - 获取 Project
    """

    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        artifact_manager: ArtifactManager,
    ):
        self.workspace_manager = workspace_manager
        self.artifact_manager = artifact_manager

        self._project: Optional[Project] = None

    def create_project(
        self,
        name: str,
        requirement: str,
        description: str = "",
    ) -> Project:
        """
        创建一个新的软件项目。
        """

        workspace = self.workspace_manager.create_workspace(name)

        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            requirement=requirement,
            workspace_path=str(workspace),
            status=ProjectStatus.CREATED,
        )

        self._project = project

        return project

    def get_project(self) -> Optional[Project]:
        """
        获取当前项目。
        """

        return self._project

    def update_status(
        self,
        status: ProjectStatus,
    ) -> None:
        """
        更新项目状态。
        """

        if self._project is None:
            raise RuntimeError("Project does not exist.")

        self._project.update_status(status)

    def delete_project(self) -> None:
        """
        删除项目。
        """

        if self._project is None:
            return

        self.workspace_manager.remove_workspace(
            self._project.name
        )

        self.artifact_manager.clear()

        self._project = None

    def exists(self) -> bool:
        """
        当前是否存在项目。
        """

        return self._project is not None