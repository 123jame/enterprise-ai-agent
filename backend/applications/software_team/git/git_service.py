from __future__ import annotations

from pathlib import Path

from app.memory.manager import MemoryManager
from app.memory.types import MemoryRecord

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.git.branch_strategy import BranchStrategy
from applications.software_team.git.commit_message_builder import (
    CommitMessageBuilder,
)
from applications.software_team.git.git_context import GitCommitInfo
from applications.software_team.git.git_context import GitContext
from applications.software_team.git.git_context import GitEventType
from applications.software_team.git.git_context import GitOperationResult
from applications.software_team.git.git_context import MergeResult
from applications.software_team.git.git_manager import GitManager
from applications.software_team.git.merge_manager import MergeManager
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.project import Project


class GitService:
    """
    Software Team Git 工作流编排服务。

    供 Pipeline / Coordinator 调用，Agent 不直接操作 Git。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        git_manager: GitManager | None = None,
        branch_strategy: BranchStrategy | None = None,
        commit_message_builder: CommitMessageBuilder | None = None,
        merge_manager: MergeManager | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._git = git_manager or GitManager(settings=self._settings)
        self._strategy = branch_strategy or BranchStrategy(
            settings=self._settings,
        )
        self._commit_builder = (
            commit_message_builder or CommitMessageBuilder()
        )
        self._merge_manager = merge_manager or MergeManager(
            git_manager=self._git,
            branch_strategy=self._strategy,
        )

    @property
    def enabled(self) -> bool:

        return (
            self._settings.enable_git
            and self._git.is_available()
        )

    def initialize_project(
        self,
        project: Project,
    ) -> GitOperationResult:

        if not self.enabled:

            return GitOperationResult(
                success=True,
                stdout="Git integration disabled.",
                metadata={"skipped": True},
            )

        workspace = Path(project.workspace_path)

        init_result = self._git.init(
            workspace,
            initial_branch=self._strategy.main_branch,
        )

        if not init_result.success:

            return init_result

        ensure_result = self._ensure_integration_branch(workspace)

        if not ensure_result.success:

            return ensure_result

        return init_result

    def _ensure_integration_branch(
        self,
        workspace: Path,
    ) -> GitOperationResult:
        """
        确保 develop（或配置的集成分支）存在。

        新仓库首次提交可能只在 feature 分支上，main 尚无 ref；
        此时返回 deferred，由 merge_agent_to_develop 从 feature 创建 develop。
        """

        develop = self._strategy.develop_branch
        main = self._strategy.main_branch

        if develop == main:

            return GitOperationResult(
                success=True,
                command="branch ensure (skipped)",
                stdout="Integration branch equals main.",
            )

        if self._git.checkout(workspace, develop).success:

            current = self._git.current_branch(workspace)
            if current != main:
                self._git.checkout(workspace, main)

            return GitOperationResult(
                success=True,
                command=f"git checkout {develop}",
                stdout=f"Branch {develop} already exists.",
            )

        if (
            self._git.checkout(workspace, main).success
            and self._git.has_commits(workspace)
        ):

            created = self._git.checkout(
                workspace,
                develop,
                create=True,
            )

            if created.success:

                self._git.checkout(workspace, main)

                return GitOperationResult(
                    success=True,
                    command=f"git checkout -b {develop}",
                    stdout=f"Created branch {develop} from {main}.",
                )

        current = self._git.current_branch(workspace)

        if current and self._git.has_commits(workspace):

            if not self._git.checkout(workspace, current).success:

                return GitOperationResult(
                    success=True,
                    command="branch ensure (deferred)",
                    stdout=(
                        f"Branch {develop} will be created during merge."
                    ),
                    metadata={"deferred": True},
                )

            created = self._git.checkout(
                workspace,
                develop,
                create=True,
            )

            if created.success:

                self._git.checkout(workspace, current)

                return GitOperationResult(
                    success=True,
                    command=f"git checkout -b {develop}",
                    stdout=f"Created branch {develop} from {current}.",
                )

        return GitOperationResult(
            success=True,
            command="branch ensure (deferred)",
            stdout=(
                f"Branch {develop} will be created after the first commit."
            ),
            metadata={"deferred": True},
        )

    def begin_agent_step(
        self,
        project: Project,
        agent_name: str,
    ) -> GitContext:
        """
        为 Agent 步骤创建 feature 分支。
        """

        if not self.enabled:

            return self.build_context(project)

        workspace = Path(project.workspace_path)
        feature_branch = self._strategy.feature_branch(
            agent_name,
            project_name=project.name,
        )

        main = self._strategy.main_branch
        develop = self._strategy.develop_branch

        self._ensure_integration_branch(workspace)

        if not self._git.checkout(workspace, develop).success:

            self._git.checkout(workspace, main)
            self._git.checkout(
                workspace,
                develop,
                create=True,
            )

        self._git.checkout(
            workspace,
            feature_branch,
            create=True,
        )

        return self.build_context(project)

    def commit_agent_step(
        self,
        *,
        project: Project,
        agent_name: str,
        artifact_manager: ArtifactManager,
        memory_manager: MemoryManager | None = None,
        session_id: str = "",
    ) -> GitCommitInfo | None:
        """
        自动 git add + commit，并关联 Artifact。
        """

        if not self.enabled:

            return None

        workspace = Path(project.workspace_path)

        status = self._git.status(workspace)

        if not status.stdout.strip():

            return None

        add_result = self._git.add(workspace, ".")

        if not add_result.success:

            return None

        artifacts = artifact_manager.find_by_owner(agent_name)
        changed = self._git.diff_stat(workspace)

        message = self._commit_builder.build(
            agent_name=agent_name,
            project=project,
            artifacts=artifacts,
            changed_summary=changed,
        )

        commit_result = self._git.commit(
            workspace,
            message,
        )

        if not commit_result.success:

            return None

        sha = self._git.last_commit_sha(workspace)
        branch = self._git.current_branch(workspace)

        artifact_ids = [
            artifact.id
            for artifact in artifacts
        ]

        artifact_manager.link_commit_to_artifacts(
            artifact_ids,
            sha,
            branch=branch,
        )

        commit_info = GitCommitInfo(
            sha=sha,
            message=message.splitlines()[0],
            branch=branch,
            agent_name=agent_name,
            artifact_ids=artifact_ids,
        )

        if memory_manager is not None and session_id:

            self.save_git_memory(
                memory_manager=memory_manager,
                session_id=session_id,
                event_type=GitEventType.COMMIT,
                content=(
                    f"Git commit by {agent_name} on {branch}: "
                    f"{commit_info.message} ({sha[:8]})"
                ),
                metadata={
                    "sha": sha,
                    "branch": branch,
                    "agent": agent_name,
                    "artifact_ids": artifact_ids,
                },
            )

        return commit_info

    def merge_agent_to_develop(
        self,
        *,
        project: Project,
        agent_name: str,
        memory_manager: MemoryManager | None = None,
        session_id: str = "",
    ) -> MergeResult | None:

        if not self.enabled or not self._settings.git_auto_merge_to_develop:

            return None

        workspace = Path(project.workspace_path)
        feature_branch = self._strategy.feature_branch(
            agent_name,
            project_name=project.name,
        )

        ensure = self._ensure_integration_branch(workspace)

        if not ensure.success:

            return MergeResult(
                success=False,
                source_branch=feature_branch,
                target_branch=self._strategy.develop_branch,
                message=ensure.error_message or "Failed to ensure develop branch",
            )

        develop = self._strategy.develop_branch

        if not self._git.checkout(workspace, develop).success:

            on_feature = self._git.checkout(workspace, feature_branch)

            if not on_feature.success:

                return MergeResult(
                    success=False,
                    source_branch=feature_branch,
                    target_branch=develop,
                    message=(
                        on_feature.error_message
                        or f"Cannot checkout feature branch {feature_branch}"
                    ),
                )

            created = self._git.checkout(
                workspace,
                develop,
                create=True,
            )

            if not created.success:

                return MergeResult(
                    success=False,
                    source_branch=feature_branch,
                    target_branch=develop,
                    message=created.error_message or "Failed to create develop branch",
                )

            self._git.checkout(workspace, feature_branch)

        result = self._merge_manager.merge_feature_to_develop(
            workspace,
            feature_branch,
        )

        if memory_manager is not None and session_id:

            self.save_git_memory(
                memory_manager=memory_manager,
                session_id=session_id,
                event_type=GitEventType.MERGE,
                content=(
                    f"Merge {feature_branch} -> "
                    f"{self._strategy.develop_branch}: "
                    f"{'success' if result.success else 'failed'}"
                ),
                metadata={
                    "source": feature_branch,
                    "target": self._strategy.develop_branch,
                    "conflicts": result.conflict_files,
                    "agent": agent_name,
                },
            )

        return result

    def finalize_pipeline(
        self,
        project: Project,
        *,
        memory_manager: MemoryManager | None = None,
        session_id: str = "",
    ) -> MergeResult | None:
        """
        Pipeline 结束时 merge develop -> main。
        """

        if (
            not self.enabled
            or not self._settings.git_finalize_to_main
        ):

            return None

        workspace = Path(project.workspace_path)

        result = self._merge_manager.merge_develop_to_main(
            workspace,
        )

        if result.success:

            self._git.tag(
                workspace,
                f"v-{project.name[:20]}",
                message=f"Release {project.name}",
            )

        if memory_manager is not None and session_id:

            self.save_git_memory(
                memory_manager=memory_manager,
                session_id=session_id,
                event_type=GitEventType.MERGE,
                content=(
                    f"Finalize merge develop -> main: "
                    f"{'success' if result.success else 'failed'}"
                ),
                metadata={
                    "source": self._strategy.develop_branch,
                    "target": self._strategy.main_branch,
                    "conflicts": result.conflict_files,
                },
            )

        return result

    def build_context(
        self,
        project: Project,
    ) -> GitContext:

        workspace = project.workspace_path

        if not self.enabled or not self._git.is_repo(workspace):

            return GitContext(
                workspace_path=workspace,
                is_initialized=False,
            )

        return GitContext(
            workspace_path=workspace,
            current_branch=self._git.current_branch(workspace),
            last_commit_sha=self._git.last_commit_sha(workspace),
            last_commit_message=self._git.last_commit_message(
                workspace
            ),
            recent_commits=self._git.log(workspace, limit=5),
            is_initialized=True,
        )

    @staticmethod
    def save_git_memory(
        *,
        memory_manager: MemoryManager,
        session_id: str,
        event_type: GitEventType,
        content: str,
        metadata: dict | None = None,
    ) -> None:

        record = MemoryRecord(
            role="assistant",
            content=content,
            metadata={
                "type": "memory",
                "category": event_type.value,
                **(metadata or {}),
            },
        )

        memory_manager.memory.save(
            session_id,
            record,
        )
