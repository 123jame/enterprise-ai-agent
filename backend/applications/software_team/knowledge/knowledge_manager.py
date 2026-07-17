from __future__ import annotations

from pathlib import Path

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.knowledge.document_indexer import DocumentIndexer
from applications.software_team.knowledge.experience_manager import ExperienceManager
from applications.software_team.knowledge.knowledge_repository import KnowledgeRepository
from applications.software_team.knowledge.knowledge_result import KnowledgeCategory
from applications.software_team.knowledge.knowledge_result import KnowledgeEntry
from applications.software_team.knowledge.knowledge_result import RetrievalMode
from applications.software_team.knowledge.lesson_learned_manager import LessonLearnedManager
from applications.software_team.knowledge.recommendation_manager import RecommendationManager
from applications.software_team.knowledge.retrieval_manager import RetrievalManager
from applications.software_team.project.models.project import Project


class KnowledgeManager:
    """
    统一知识管理入口，协调 Repository / Indexer / Retrieval / Recommendation。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        repository: KnowledgeRepository | None = None,
        indexer: DocumentIndexer | None = None,
        retrieval: RetrievalManager | None = None,
        recommendation: RecommendationManager | None = None,
        experience: ExperienceManager | None = None,
        lessons: LessonLearnedManager | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._repo = repository or KnowledgeRepository(settings=self._settings)
        self._indexer = indexer or DocumentIndexer(
            settings=self._settings,
            repository=self._repo,
        )
        self._retrieval = retrieval or RetrievalManager(
            settings=self._settings,
            repository=self._repo,
            indexer=self._indexer,
        )
        self._recommendation = recommendation or RecommendationManager(
            settings=self._settings,
            repository=self._repo,
        )
        self._experience = experience or ExperienceManager(
            settings=self._settings,
            repository=self._repo,
        )
        self._lessons = lessons or LessonLearnedManager(
            settings=self._settings,
            repository=self._repo,
        )

    @property
    def repository(self) -> KnowledgeRepository:

        return self._repo

    @property
    def indexer(self) -> DocumentIndexer:

        return self._indexer

    @property
    def retrieval(self) -> RetrievalManager:

        return self._retrieval

    @property
    def recommendation(self) -> RecommendationManager:

        return self._recommendation

    @property
    def experience(self) -> ExperienceManager:

        return self._experience

    @property
    def lessons(self) -> LessonLearnedManager:

        return self._lessons

    def capture_from_file(
        self,
        project: Project,
        *,
        file_path: str | Path,
        category: KnowledgeCategory,
        agent_name: str = "",
    ) -> KnowledgeEntry | None:

        workspace = Path(project.workspace_path)
        path = Path(file_path)

        if not path.is_absolute():

            path = workspace / path

        if not path.is_file():

            return None

        try:

            content = path.read_text(encoding="utf-8", errors="replace")[:10000]

        except OSError:

            return None

        entry = KnowledgeEntry.create(
            title=path.name,
            category=category,
            content=content,
            source_path=str(path.relative_to(workspace)),
            project_id=project.id,
            agent_name=agent_name,
        )

        self._repo.save(workspace, entry)
        self._indexer.index_entry(workspace, entry)

        return entry

    def index_project(self, project: Project) -> int:

        records = self._indexer.index_workspace(
            project.workspace_path,
            project_id=project.id,
        )

        return len(records)

    def search(
        self,
        project: Project,
        query: str,
        *,
        mode: RetrievalMode | None = None,
    ):

        return self._retrieval.search(
            project.workspace_path,
            query,
            mode=mode,
        )

    def recommend(
        self,
        project: Project,
        *,
        agent_name: str,
        task: str = "",
        query: str = "",
    ):

        hits = []

        if query:

            retrieval = self.search(project, query)
            hits = retrieval.hits

        return self._recommendation.recommend(
            project,
            agent_name=agent_name,
            task=task,
            retrieval_hits=hits,
        )

    def get_entry_count(self, project: Project) -> int:

        return len(self._repo.list_entries(project.workspace_path))
