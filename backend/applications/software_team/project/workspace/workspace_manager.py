from __future__ import annotations

import shutil
from pathlib import Path


class WorkspaceManager:
    """
    项目工作空间管理器。

    负责：
    - 创建项目目录
    - 创建标准子目录
    - 删除工作空间
    - 判断是否存在
    - 获取目录路径
    """

    DEFAULT_DIRS = (
        "backend",
        "frontend",
        "database",
        "docs",
        "tests",
        "output",
        "temp",
    )

    def __init__(self, workspace_root: str = "workspace"):
        self.workspace_root = Path(workspace_root)

    def create_workspace(self, project_name: str) -> Path:
        """
        创建项目工作空间。
        """

        project_dir = self.workspace_root / self._normalize(project_name)

        project_dir.mkdir(parents=True, exist_ok=True)

        for folder in self.DEFAULT_DIRS:
            (project_dir / folder).mkdir(exist_ok=True)

        return project_dir

    def exists(self, project_name: str) -> bool:
        """
        判断项目是否存在。
        """

        return self.get_workspace(project_name).exists()

    def remove_workspace(self, project_name: str) -> None:
        """
        删除整个工作空间。
        """

        workspace = self.get_workspace(project_name)

        if workspace.exists():
            shutil.rmtree(workspace)

    def get_workspace(self, project_name: str) -> Path:
        """
        获取项目工作目录。
        """

        return self.workspace_root / self._normalize(project_name)

    def get_subdirectory(
        self,
        project_name: str,
        folder: str,
    ) -> Path:
        """
        获取指定子目录。
        """

        return self.get_workspace(project_name) / folder

    @staticmethod
    def _normalize(project_name: str) -> str:
        """
        将项目名称转换成目录名称。
        """

        return (
            project_name
            .strip()
            .lower()
            .replace(" ", "_")
        )