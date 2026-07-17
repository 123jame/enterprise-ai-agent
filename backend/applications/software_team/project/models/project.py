from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from .project_status import ProjectStatus


class Project(BaseModel):
    """
    软件开发项目模型。

    Project 是 AI Software Development Team 的核心对象，
    描述当前正在开发的软件项目。

    所有 Agent（Product、Architect、Backend、Frontend、QA、
    Documentation 等）都围绕 Project 进行协作。
    """

    # ==========================================================
    # Basic Information
    # ==========================================================

    id: str = Field(
        description="项目唯一ID"
    )

    name: str = Field(
        description="项目名称"
    )

    description: str = Field(
        default="",
        description="项目描述"
    )

    requirement: str = Field(
        description="用户原始需求"
    )

    tech_stack: List[str] = Field(
        default_factory=list,
        description="项目技术栈"
    )

    # ==========================================================
    # Project State
    # ==========================================================

    status: ProjectStatus = Field(
        default=ProjectStatus.CREATED,
        description="项目当前状态"
    )

    workspace_path: str = Field(
        default="",
        description="项目工作目录"
    )

    # ==========================================================
    # Runtime Data
    # ==========================================================

    tasks: List[str] = Field(
        default_factory=list,
        description="项目任务列表"
    )

    artifacts: List[str] = Field(
        default_factory=list,
        description="项目产物列表"
    )

    # ==========================================================
    # Metadata
    # ==========================================================

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="创建时间"
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="最后更新时间"
    )

    # ==========================================================
    # Helper Methods
    # ==========================================================

    def update_timestamp(self) -> None:
        """
        更新最后修改时间。
        """
        self.updated_at = datetime.utcnow()

    def add_task(self, task: str) -> None:
        """
        添加项目任务。
        """
        self.tasks.append(task)
        self.update_timestamp()

    def add_artifact(self, artifact: str) -> None:
        """
        添加项目产物。
        """
        self.artifacts.append(artifact)
        self.update_timestamp()

    def update_status(self, status: ProjectStatus) -> None:
        """
        更新项目状态。
        """
        self.status = status
        self.update_timestamp()