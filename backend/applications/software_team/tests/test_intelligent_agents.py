"""
P5 智能 Agent 集成测试（Mock LLM，无需 API Key）。

运行:
    cd backend
    python -m applications.software_team.tests.test_intelligent_agents
"""

from __future__ import annotations

import tempfile
from unittest.mock import MagicMock
from uuid import uuid4

from app.agents.types import AgentContext
from app.agents.types import AgentResult
from app.memory.manager import MemoryManager

from applications.software_team.agents.architect.architect_agent import (
    ArchitectAgent,
)
from applications.software_team.agents.backend.backend_agent import BackendAgent
from applications.software_team.agents.base.coordinator_context import (
    CoordinatorContext,
)
from applications.software_team.agents.documentation.documentation_agent import (
    DocumentationAgent,
)
from applications.software_team.agents.frontend.frontend_agent import FrontendAgent
from applications.software_team.agents.product.product_agent import ProductAgent
from applications.software_team.agents.qa.qa_agent import QAAgent
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.project import Project
from applications.software_team.project.models.project_status import ProjectStatus
from applications.software_team.project.workspace.workspace_manager import (
    WorkspaceManager,
)
from applications.software_team.runtime.team_agent_runtime import TeamAgentRuntime


def _build_context(
    project: Project,
    *,
    metadata: dict | None = None,
) -> CoordinatorContext:

    return CoordinatorContext(
        session_id=f"test_{uuid4().hex[:8]}",
        user_message=project.requirement,
        project=project,
        metadata=metadata or {},
        shared_context={"requirement": project.requirement},
    )


def _build_runtime(
    llm_content: str,
) -> TeamAgentRuntime:

    mock_executor = MagicMock()
    mock_executor.run.return_value = AgentResult(
        success=True,
        model="mock-llm",
        content=llm_content,
    )

    settings = SoftwareTeamSettings(
        enable_template_fallback=False,
    )

    return TeamAgentRuntime(
        settings=settings,
        memory_manager=MemoryManager(),
        agent_executor=mock_executor,
    )


def _build_project(tmp: str) -> tuple[Project, ArtifactManager, WorkspaceManager]:

    workspace_manager = WorkspaceManager(workspace_root=tmp)

    project = Project(
        id="proj_test",
        name="test_project",
        requirement="开发一个图书管理系统",
        workspace_path=str(workspace_manager.create_workspace("test_project")),
        status=ProjectStatus.PLANNING,
        tech_stack=["Python", "FastAPI"],
    )

    return project, ArtifactManager(), workspace_manager


def test_product_agent_intelligent_loop() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        project, artifact_manager, workspace_manager = _build_project(tmp)
        runtime = _build_runtime("# PRD\n\nMock PRD content from LLM.")

        agent = ProductAgent(
            project=project,
            artifact_manager=artifact_manager,
            workspace_manager=workspace_manager,
            team_agent_runtime=runtime,
        )

        result = agent.execute_team(_build_context(project))

        assert result.success is True
        assert result.model == "mock-llm"
        assert artifact_manager.count() == 1
        assert "PRD.md" in artifact_manager.list()[0].name


def test_architect_agent_requires_prd() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        project, artifact_manager, workspace_manager = _build_project(tmp)
        runtime = _build_runtime("# Architecture\n\nMock architecture.")

        from pathlib import Path

        from applications.software_team.project.models.artifact import Artifact

        prd_path = Path(project.workspace_path) / "docs" / "PRD.md"
        prd_path.parent.mkdir(parents=True, exist_ok=True)
        prd_path.write_text("# PRD\n", encoding="utf-8")

        artifact_manager.add(
            Artifact(
                id="a1",
                name="PRD.md",
                type="document",
                path=str(prd_path),
                owner="ProductAgent",
            )
        )

        agent = ArchitectAgent(
            project=project,
            artifact_manager=artifact_manager,
            workspace_manager=workspace_manager,
            team_agent_runtime=runtime,
        )

        result = agent.execute_team(_build_context(project))

        assert result.success is True
        assert result.model == "mock-llm"


def test_backend_agent_intelligent_loop_with_tool_written_files() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        project, artifact_manager, workspace_manager = _build_project(tmp)

        from pathlib import Path

        from applications.software_team.project.models.artifact import Artifact

        arch_path = Path(project.workspace_path) / "docs" / "Architecture.md"
        arch_path.parent.mkdir(parents=True, exist_ok=True)
        arch_path.write_text("# Architecture\n", encoding="utf-8")

        artifact_manager.add(
            Artifact(
                id="a2",
                name="Architecture.md",
                type="document",
                path=f"{project.workspace_path}/docs/Architecture.md",
                owner="ArchitectAgent",
            )
        )

        runtime = _build_runtime("Backend files created via tools.")

        backend_dir = Path(project.workspace_path) / "backend"
        backend_dir.mkdir(exist_ok=True)
        (backend_dir / "main.py").write_text(
            "from fastapi import FastAPI\napp = FastAPI()\n",
            encoding="utf-8",
        )
        (backend_dir / "requirements.txt").write_text(
            "fastapi\n",
            encoding="utf-8",
        )

        agent = BackendAgent(
            project=project,
            artifact_manager=artifact_manager,
            workspace_manager=workspace_manager,
            team_agent_runtime=runtime,
        )

        result = agent.execute_team(_build_context(project))

        assert result.success is True
        assert any(
            artifact.name == "backend"
            for artifact in artifact_manager.list()
        )


def test_template_fallback_when_llm_fails() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        project, artifact_manager, workspace_manager = _build_project(tmp)

        mock_executor = MagicMock()
        mock_executor.run.return_value = AgentResult(
            success=False,
            model="",
            content="LLM unavailable",
        )

        settings = SoftwareTeamSettings(
            enable_template_fallback=True,
        )

        runtime = TeamAgentRuntime(
            settings=settings,
            memory_manager=MemoryManager(),
            agent_executor=mock_executor,
        )

        agent = ProductAgent(
            project=project,
            artifact_manager=artifact_manager,
            workspace_manager=workspace_manager,
            team_agent_runtime=runtime,
        )

        result = agent.execute_team(_build_context(project))

        assert result.success is True
        assert result.model == "template_fallback"


def main() -> None:

    test_product_agent_intelligent_loop()
    test_architect_agent_requires_prd()
    test_backend_agent_intelligent_loop_with_tool_written_files()
    test_template_fallback_when_llm_fails()
    print("All P5 intelligent agent tests passed.")


if __name__ == "__main__":

    main()
