from applications.software_team.knowledge.knowledge_result import ExperienceRecord
from applications.software_team.knowledge.knowledge_result import ExperienceType
from applications.software_team.knowledge.knowledge_result import IndexRecord
from applications.software_team.knowledge.knowledge_result import KnowledgeCategory
from applications.software_team.knowledge.knowledge_result import KnowledgeContext
from applications.software_team.knowledge.knowledge_result import KnowledgeEntry
from applications.software_team.knowledge.knowledge_result import KnowledgeEventType
from applications.software_team.knowledge.knowledge_result import KnowledgePipelineResult
from applications.software_team.knowledge.knowledge_result import LessonLearned
from applications.software_team.knowledge.knowledge_result import Recommendation
from applications.software_team.knowledge.knowledge_result import RecommendationResult
from applications.software_team.knowledge.knowledge_result import RetrievalHit
from applications.software_team.knowledge.knowledge_result import RetrievalMode
from applications.software_team.knowledge.knowledge_result import RetrievalResult

__all__ = [
    "DocumentIndexer",
    "ExperienceManager",
    "ExperienceRecord",
    "ExperienceType",
    "IndexRecord",
    "KnowledgeCategory",
    "KnowledgeContext",
    "KnowledgeEntry",
    "KnowledgeEventType",
    "KnowledgeManager",
    "KnowledgePipelineResult",
    "KnowledgeRepository",
    "KnowledgeService",
    "LessonLearned",
    "LessonLearnedManager",
    "Recommendation",
    "RecommendationManager",
    "RecommendationResult",
    "RetrievalHit",
    "RetrievalManager",
    "RetrievalMode",
    "RetrievalResult",
]


def __getattr__(name: str):

    if name == "DocumentIndexer":
        from applications.software_team.knowledge.document_indexer import (
            DocumentIndexer,
        )

        return DocumentIndexer

    if name == "ExperienceManager":
        from applications.software_team.knowledge.experience_manager import (
            ExperienceManager,
        )

        return ExperienceManager

    if name == "KnowledgeManager":
        from applications.software_team.knowledge.knowledge_manager import (
            KnowledgeManager,
        )

        return KnowledgeManager

    if name == "KnowledgeRepository":
        from applications.software_team.knowledge.knowledge_repository import (
            KnowledgeRepository,
        )

        return KnowledgeRepository

    if name == "KnowledgeService":
        from applications.software_team.knowledge.knowledge_service import (
            KnowledgeService,
        )

        return KnowledgeService

    if name == "LessonLearnedManager":
        from applications.software_team.knowledge.lesson_learned_manager import (
            LessonLearnedManager,
        )

        return LessonLearnedManager

    if name == "RecommendationManager":
        from applications.software_team.knowledge.recommendation_manager import (
            RecommendationManager,
        )

        return RecommendationManager

    if name == "RetrievalManager":
        from applications.software_team.knowledge.retrieval_manager import (
            RetrievalManager,
        )

        return RetrievalManager

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
