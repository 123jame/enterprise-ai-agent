from applications.software_team.config.settings import (
    SoftwareTeamSettings,
)
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.artifact import Artifact
from applications.software_team.project.models.project_status import (
    ProjectStatus,
)
from applications.software_team.project.services.project_service import (
    ProjectService,
)
from applications.software_team.project.workspace.workspace_manager import (
    WorkspaceManager,
)


def main():

    print("=" * 60)
    print("AI Software Team Demo")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------

    settings = SoftwareTeamSettings()

    workspace_manager = WorkspaceManager(
        workspace_root=settings.workspace_root
    )

    artifact_manager = ArtifactManager()

    project_service = ProjectService(
        workspace_manager=workspace_manager,
        artifact_manager=artifact_manager,
    )

    # ------------------------------------------------------------------
    # 创建项目
    # ------------------------------------------------------------------

    project = project_service.create_project(
        name="Library Management System",
        description="图书管理系统",
        requirement="开发一个图书管理系统",
    )

    print("\nProject Created")
    print(project)

    # ------------------------------------------------------------------
    # 创建一个 Artifact
    # ------------------------------------------------------------------

    artifact = Artifact(
        id="artifact_001",
        name="README.md",
        type="document",
        path=f"{project.workspace_path}/docs/README.md",
        owner="DocumentationAgent",
    )

    artifact_manager.add(artifact)

    print("\nArtifact Count")
    print(artifact_manager.count())

    # ------------------------------------------------------------------
    # 修改状态
    # ------------------------------------------------------------------

    project_service.update_status(
        ProjectStatus.PLANNING
    )

    print("\nCurrent Status")
    print(project.status)

    # ------------------------------------------------------------------
    # 查看 Workspace
    # ------------------------------------------------------------------

    print("\nWorkspace")
    print(project.workspace_path)

    # ------------------------------------------------------------------
    # 查看 Artifact
    # ------------------------------------------------------------------

    print("\nArtifacts")

    for item in artifact_manager.list():
        print(item)

    print("\nDemo Finished")


if __name__ == "__main__":
    main()