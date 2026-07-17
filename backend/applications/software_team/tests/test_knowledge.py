"""
P11 Knowledge Management 测试。

运行:
    cd backend
    python -m applications.software_team.tests.test_knowledge
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.memory.manager import MemoryManager

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.knowledge.document_indexer import DocumentIndexer
from applications.software_team.knowledge.experience_manager import ExperienceManager
from applications.software_team.knowledge.knowledge_manager import KnowledgeManager
from applications.software_team.knowledge.knowledge_repository import KnowledgeRepository
from applications.software_team.knowledge.knowledge_result import KnowledgeCategory
from applications.software_team.knowledge.knowledge_result import KnowledgeContext
from applications.software_team.knowledge.knowledge_result import KnowledgeEntry
from applications.software_team.knowledge.knowledge_result import RetrievalMode
from applications.software_team.knowledge.knowledge_service import KnowledgeService
from applications.software_team.knowledge.lesson_learned_manager import LessonLearnedManager
from applications.software_team.knowledge.recommendation_manager import RecommendationManager
from applications.software_team.knowledge.retrieval_manager import RetrievalManager
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.project import Project
from applications.software_team.project.models.project_status import ProjectStatus


def _sample_project(root: Path) -> Project:

    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "PRD.md").write_text(
        "# PRD\n图书管理系统需求：用户管理、借阅管理\n",
        encoding="utf-8",
    )
    (docs / "Architecture.md").write_text(
        "# Architecture\nFastAPI backend + React frontend\n",
        encoding="utf-8",
    )
    (root / "backend").mkdir(exist_ok=True)
    (root / "backend" / "main.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n",
        encoding="utf-8",
    )

    return Project(
        id="proj-kb-1",
        name="Library System",
        requirement="开发图书管理系统",
        workspace_path=str(root),
        status=ProjectStatus.PLANNING,
        tech_stack=["python", "fastapi"],
    )


def test_knowledge_repository() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        entry = KnowledgeEntry.create(
            title="Test PRD",
            category=KnowledgeCategory.PRD,
            content="User stories and requirements",
            project_id="p1",
        )

        repo = KnowledgeRepository()
        path = repo.save(root, entry)

        loaded = repo.load(root, entry.id)

        assert Path(path).is_file()
        assert loaded is not None
        assert loaded.title == "Test PRD"
        assert len(repo.list_entries(root)) == 1
        print("KnowledgeRepository: PASS")


def test_document_indexer() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        project = _sample_project(root)

        indexer = DocumentIndexer()
        records = indexer.index_workspace(
            project.workspace_path,
            project_id=project.id,
        )

        assert len(records) >= 3
        assert any(r.document_type == "markdown" for r in records)

        reloaded = indexer.load_index(project.workspace_path)
        assert len(reloaded) >= 3
        print("DocumentIndexer: PASS")


def test_retrieval_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        project = _sample_project(root)

        repo = KnowledgeRepository()
        entry = KnowledgeEntry.create(
            title="FastAPI Pattern",
            category=KnowledgeCategory.CODE_PATTERN,
            content="Use FastAPI with uvicorn for backend API",
            project_id=project.id,
        )
        repo.save(root, entry)

        DocumentIndexer().index_workspace(root)

        for mode in (
            RetrievalMode.KEYWORD,
            RetrievalMode.EMBEDDING,
            RetrievalMode.HYBRID,
        ):

            result = RetrievalManager().search(
                root,
                "FastAPI backend",
                mode=mode,
            )

            assert result.success is True

        print("RetrievalManager: PASS")


def test_recommendation_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        project = _sample_project(root)

        repo = KnowledgeRepository()
        repo.save(
            root,
            KnowledgeEntry.create(
                title="Arch doc",
                category=KnowledgeCategory.ARCHITECTURE,
                content="System architecture for library",
                agent_name="ArchitectAgent",
                project_id=project.id,
            ),
        )

        result = RecommendationManager().recommend(
            project,
            agent_name="BackendAgent",
            task="生成 FastAPI 后端",
        )

        assert result.success is True
        assert len(result.recommendations) >= 1
        print("RecommendationManager: PASS")


def test_experience_and_lessons() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        project = _sample_project(root)

        experience = ExperienceManager()
        success = experience.capture_success(
            project,
            agent_name="BackendAgent",
            summary="Backend generated successfully",
        )
        failure = experience.capture_failure(
            project,
            agent_name="QAAgent",
            summary="Tests failed",
        )

        assert success.experience_type.value == "success"
        assert failure.experience_type.value == "failure"

        lessons = LessonLearnedManager()
        lesson = lessons.record_from_failure(
            project,
            agent_name="QAAgent",
            error_message="pytest assertion failed",
        )

        assert lesson is not None
        assert len(lessons.list_lessons(root)) == 1
        assert len(experience.list_experiences(root)) == 2
        print("ExperienceManager & LessonLearnedManager: PASS")


def test_knowledge_manager() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        project = _sample_project(root)

        manager = KnowledgeManager()
        count = manager.index_project(project)

        assert count >= 3

        retrieval = manager.search(project, "图书管理")
        assert retrieval.success is True

        recommend = manager.recommend(
            project,
            agent_name="ProductAgent",
            task="生成 PRD",
            query="图书管理",
        )

        assert len(recommend.recommendations) >= 1
        print("KnowledgeManager: PASS")


def test_knowledge_service_lifecycle() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)
        project = _sample_project(root)

        settings = SoftwareTeamSettings(enable_knowledge_management=True)
        service = KnowledgeService(settings=settings)
        memory = MemoryManager()
        artifacts = ArtifactManager()

        init_result = service.initialize(
            project,
            artifact_manager=artifacts,
            memory_manager=memory,
            session_id="kb-life",
        )

        assert init_result.success is True

        prep = service.prepare_for_agent(
            project,
            agent_name="BackendAgent",
            task="生成 FastAPI 后端",
            memory_manager=memory,
            session_id="kb-life",
        )

        assert prep.retrieval is not None
        assert prep.recommendations is not None
        assert prep.context.retrieval_summary

        update = service.update_after_agent(
            project,
            agent_name="BackendAgent",
            success=True,
            summary="Backend created",
            memory_manager=memory,
            session_id="kb-life",
        )

        assert update.success is True

        final = service.finalize(
            project,
            artifact_manager=artifacts,
            memory_manager=memory,
            session_id="kb-life",
            pipeline_success=True,
        )

        assert final.success is True
        assert Path(final.report_path).is_file()
        assert len(artifacts.find_knowledge_artifacts()) >= 2

        memory_context = memory.load("kb-life")
        categories = {
            r.metadata.get("category")
            for r in memory_context.records
        }
        assert "knowledge_history" in categories
        assert "recommendation_history" in categories
        assert "experience_history" in categories
        print("KnowledgeService lifecycle: PASS")


def test_team_prompt_builder_knowledge_context() -> None:

    from app.agents.types import AgentContext

    from applications.software_team.agents.base.coordinator_context import (
        CoordinatorContext,
    )
    from applications.software_team.prompt.team_prompt_builder import (
        TeamPromptBuilder,
    )

    project = Project(
        id="p1",
        name="Demo",
        requirement="demo",
        workspace_path="/tmp/ws",
        status=ProjectStatus.PLANNING,
    )

    context = CoordinatorContext.from_agent_context(
        context=AgentContext(
            session_id="s1",
            user_message="build",
            metadata={"knowledge_context": True},
        ),
        project=project,
    )

    know_ctx = KnowledgeContext(
        retrieval_summary="Retrieval (hybrid): 2 hit(s)",
        recommendation_summary="Recommendations for BackendAgent: 3",
        best_practices="FastAPI 项目使用 main.py 结构",
        lessons_learned="- Failure in QAAgent: review test coverage",
        historical_solutions="[solution] Fix import error",
    )

    builder = TeamPromptBuilder()
    messages = builder.build(
        "ProductAgent",
        context,
        ArtifactManager(),
        knowledge_context=know_ctx,
    )

    combined = "\n".join(m.content for m in messages)
    assert "Knowledge Context" in combined
    assert "Lessons Learned" in combined
    print("TeamPromptBuilder knowledge: PASS")


def main() -> None:

    test_knowledge_repository()
    test_document_indexer()
    test_retrieval_manager()
    test_recommendation_manager()
    test_experience_and_lessons()
    test_knowledge_manager()
    test_knowledge_service_lifecycle()
    test_team_prompt_builder_knowledge_context()
    print("\nAll P11 knowledge tests passed.")


if __name__ == "__main__":

    main()
