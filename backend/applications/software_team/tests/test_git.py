"""
P7 Git Collaboration 测试。

运行:
    cd backend
    python -m applications.software_team.tests.test_git
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.git.branch_strategy import BranchStrategy
from applications.software_team.git.commit_message_builder import (
    CommitMessageBuilder,
)
from applications.software_team.git.git_manager import GitManager
from applications.software_team.git.git_service import GitService
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.artifact import Artifact
from applications.software_team.project.models.project import Project
from applications.software_team.project.models.project_status import ProjectStatus


def test_git_manager_init_and_commit() -> None:

    if shutil.which("git") is None:

        print("Skip: git not installed")
        return

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        git = GitManager()

        assert git.init(root).success is True

        (root / "README.md").write_text("# test\n", encoding="utf-8")

        assert git.add(root, ".").success is True
        assert git.commit(root, "chore: initial commit").success is True

        assert git.last_commit_sha(root)
        assert git.log(root)


def test_commit_message_builder() -> None:

    project = Project(
        id="p1",
        name="Library System",
        requirement="build library",
        workspace_path="/tmp/ws",
        status=ProjectStatus.PLANNING,
    )

    builder = CommitMessageBuilder()
    message = builder.build(
        agent_name="BackendAgent",
        project=project,
        artifacts=[
            Artifact(
                id="a1",
                name="backend",
                type="directory",
                path="/tmp/ws/backend",
                owner="BackendAgent",
            )
        ],
    )

    assert message.startswith("feat(backend):")


def test_branch_strategy() -> None:

    strategy = BranchStrategy()

    assert strategy.main_branch == "main"
    assert strategy.feature_branch("BackendAgent").startswith("feature/")


def test_git_service_commit_links_artifacts() -> None:

    if shutil.which("git") is None:

        print("Skip: git not installed")
        return

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        project = Project(
            id="p1",
            name="demo",
            requirement="demo",
            workspace_path=str(root),
            status=ProjectStatus.DEVELOPING,
        )

        settings = SoftwareTeamSettings(
            enable_git=True,
            git_auto_merge_to_develop=False,
            git_finalize_to_main=False,
        )

        service = GitService(settings=settings)
        am = ArtifactManager()

        service.initialize_project(project)

        (root / "docs").mkdir()
        (root / "docs" / "PRD.md").write_text("# PRD\n", encoding="utf-8")

        artifact = Artifact(
            id="art1",
            name="PRD.md",
            type="document",
            path=str(root / "docs" / "PRD.md"),
            owner="ProductAgent",
        )

        am.add(artifact)

        service.begin_agent_step(project, "ProductAgent")

        commit = service.commit_agent_step(
            project=project,
            agent_name="ProductAgent",
            artifact_manager=am,
        )

        assert commit is not None
        assert am.find_by_commit(commit.sha)


def main() -> None:

    test_commit_message_builder()
    test_branch_strategy()
    test_git_manager_init_and_commit()
    test_git_service_commit_links_artifacts()
    print("All P7 Git tests passed.")


if __name__ == "__main__":

    main()
