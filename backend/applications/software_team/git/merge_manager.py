from __future__ import annotations

from pathlib import Path

from applications.software_team.git.branch_strategy import BranchStrategy
from applications.software_team.git.git_context import MergeResult
from applications.software_team.git.git_manager import GitManager


class MergeManager:
    """
    负责 Git Merge、冲突检测与结果汇总。
    """

    def __init__(
        self,
        git_manager: GitManager | None = None,
        branch_strategy: BranchStrategy | None = None,
    ):

        self._git = git_manager or GitManager()
        self._strategy = branch_strategy or BranchStrategy()

    def merge(
        self,
        workspace: str | Path,
        *,
        source_branch: str,
        target_branch: str,
    ) -> MergeResult:
        """
        切换到 target 分支并 merge source 分支。
        """

        workspace = Path(workspace).resolve()

        checkout = self._git.checkout(
            workspace,
            target_branch,
        )

        if not checkout.success:

            return MergeResult(
                success=False,
                source_branch=source_branch,
                target_branch=target_branch,
                message=checkout.error_message,
                stderr=checkout.stderr,
            )

        merge_result = self._git.merge(
            workspace,
            source_branch,
        )

        conflicts = self._git.get_conflict_files(workspace)

        return MergeResult(
            success=merge_result.success and not conflicts,
            source_branch=source_branch,
            target_branch=target_branch,
            has_conflicts=bool(conflicts),
            conflict_files=conflicts,
            message=(
                "Merge completed"
                if merge_result.success and not conflicts
                else merge_result.error_message or "Merge failed"
            ),
            stdout=merge_result.stdout,
            stderr=merge_result.stderr,
        )

    def merge_feature_to_develop(
        self,
        workspace: str | Path,
        feature_branch: str,
    ) -> MergeResult:

        return self.merge(
            workspace,
            source_branch=feature_branch,
            target_branch=self._strategy.develop_branch,
        )

    def merge_develop_to_main(
        self,
        workspace: str | Path,
    ) -> MergeResult:

        workspace = Path(workspace).resolve()
        develop = self._strategy.develop_branch
        main = self._strategy.main_branch

        if develop == main:

            return MergeResult(
                success=True,
                source_branch=develop,
                target_branch=main,
                message="develop equals main, skipped",
            )

        on_develop = self._git.checkout(workspace, develop)

        if not on_develop.success:

            return MergeResult(
                success=False,
                source_branch=develop,
                target_branch=main,
                message=(
                    on_develop.error_message
                    or f"Cannot checkout {develop}"
                ),
                stderr=on_develop.stderr,
            )

        on_main = self._git.checkout(workspace, main)

        if not on_main.success:

            created = self._git.checkout(
                workspace,
                main,
                create=True,
            )

            if not created.success:

                return MergeResult(
                    success=False,
                    source_branch=develop,
                    target_branch=main,
                    message=(
                        created.error_message
                        or f"Failed to create {main} from {develop}"
                    ),
                    stderr=created.stderr,
                )

            return MergeResult(
                success=True,
                source_branch=develop,
                target_branch=main,
                message=f"Created {main} from {develop}",
            )

        return self.merge(
            workspace,
            source_branch=develop,
            target_branch=main,
        )
