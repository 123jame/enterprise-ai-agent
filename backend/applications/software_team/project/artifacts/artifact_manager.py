from __future__ import annotations

from typing import Dict
from typing import List
from typing import Optional

from applications.software_team.project.models.artifact import Artifact


class ArtifactManager:
    """
    软件开发产物管理器。

    负责统一管理项目开发过程中产生的所有 Artifact。
    """

    def __init__(self):
        self._artifacts: Dict[str, Artifact] = {}

    def add(self, artifact: Artifact) -> None:
        """
        添加一个 Artifact。
        """
        self._artifacts[artifact.id] = artifact

    def remove(self, artifact_id: str) -> None:
        """
        删除一个 Artifact。
        """
        self._artifacts.pop(artifact_id, None)

    def get(self, artifact_id: str) -> Optional[Artifact]:
        """
        根据 ID 获取 Artifact。
        """
        return self._artifacts.get(artifact_id)

    def list(self) -> List[Artifact]:
        """
        获取所有 Artifact。
        """
        return list(self._artifacts.values())

    def exists(self, artifact_id: str) -> bool:
        """
        判断 Artifact 是否存在。
        """
        return artifact_id in self._artifacts

    def clear(self) -> None:
        """
        清空所有 Artifact。
        """
        self._artifacts.clear()

    def count(self) -> int:
        """
        返回 Artifact 数量。
        """
        return len(self._artifacts)

    def find_by_owner(
        self,
        owner: str,
    ) -> List[Artifact]:
        """
        根据 Agent 查询产物。
        """
        return [
            artifact
            for artifact in self._artifacts.values()
            if artifact.owner == owner
        ]

    def find_by_type(
        self,
        artifact_type: str,
    ) -> List[Artifact]:
        """
        根据类型查询。
        """
        return [
            artifact
            for artifact in self._artifacts.values()
            if artifact.type == artifact_type
        ]

    def link_commit_to_artifacts(
        self,
        artifact_ids: list[str],
        commit_sha: str,
        *,
        branch: str = "",
    ) -> None:
        """
        将 Artifact 与 Git Commit 关联。
        """

        for artifact_id in artifact_ids:

            artifact = self._artifacts.get(artifact_id)

            if artifact is None:

                continue

            artifact.metadata["git_commit"] = commit_sha

            if branch:

                artifact.metadata["git_branch"] = branch

    def find_by_commit(
        self,
        commit_sha: str,
    ) -> List[Artifact]:
        """
        根据 Git Commit SHA 查询产物。
        """

        return [
            artifact
            for artifact in self._artifacts.values()
            if artifact.metadata.get("git_commit") == commit_sha
        ]

    def register_deployment_artifact(
        self,
        artifact: Artifact,
    ) -> None:
        """
        注册部署相关产物（Dockerfile / Release Notes 等）。
        """

        artifact.metadata.setdefault("stage", "deployment")
        self.add(artifact)

    def find_deployment_artifacts(self) -> List[Artifact]:
        """
        查询所有部署产物。
        """

        deployment_types = {
            "deployment",
            "deployment_script",
            "deployment_package",
            "release_notes",
        }

        return [
            artifact
            for artifact in self._artifacts.values()
            if artifact.type in deployment_types
        ]

    def register_operation_artifact(
        self,
        artifact: Artifact,
    ) -> None:
        """
        注册运维相关产物（Incident / Maintenance / Operation Report）。
        """

        artifact.metadata.setdefault("stage", "operations")
        self.add(artifact)

    def find_operation_artifacts(self) -> List[Artifact]:
        """
        查询所有运维产物。
        """

        operation_types = {
            "operation_report",
            "incident_report",
            "maintenance_report",
        }

        return [
            artifact
            for artifact in self._artifacts.values()
            if artifact.type in operation_types
        ]

    def register_management_artifact(
        self,
        artifact: Artifact,
    ) -> None:
        """
        注册项目管理产物（Plan / Task List / Reports）。
        """

        artifact.metadata.setdefault("stage", "management")
        self.add(artifact)

    def find_management_artifacts(self) -> List[Artifact]:
        """
        查询所有项目管理产物。
        """

        management_types = {
            "project_plan",
            "task_list",
            "risk_report",
            "progress_report",
            "milestone_report",
        }

        return [
            artifact
            for artifact in self._artifacts.values()
            if artifact.type in management_types
        ]

    def register_knowledge_artifact(
        self,
        artifact: Artifact,
    ) -> None:
        """
        注册知识管理产物（Report / Best Practice / Lessons Learned）。
        """

        artifact.metadata.setdefault("stage", "knowledge")
        self.add(artifact)

    def find_knowledge_artifacts(self) -> List[Artifact]:
        """
        查询所有知识产物。
        """

        knowledge_types = {
            "knowledge_report",
            "best_practice",
            "architecture_pattern",
            "lessons_learned",
        }

        return [
            artifact
            for artifact in self._artifacts.values()
            if artifact.type in knowledge_types
        ]

    def register_platform_artifact(
        self,
        artifact: Artifact,
    ) -> None:
        """
        注册平台级产物（Organization / Project / Knowledge / Deployment）。
        """

        artifact.metadata.setdefault("stage", "platform")
        self.add(artifact)

    def find_by_scope(
        self,
        scope: str,
    ) -> List[Artifact]:
        """
        按平台作用域查询产物。

        scope: organization | project | knowledge | deployment
        """

        return [
            artifact
            for artifact in self._artifacts.values()
            if artifact.metadata.get("platform_scope") == scope
        ]