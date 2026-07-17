from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class KnowledgeEventType(str, Enum):
    """
    Memory 知识事件类型。
    """

    CAPTURE = "knowledge_history"
    RETRIEVAL = "knowledge_history"
    RECOMMENDATION = "recommendation_history"
    EXPERIENCE = "experience_history"
    LESSON = "knowledge_history"
    IMPROVEMENT = "experience_history"


class KnowledgeCategory(str, Enum):
    """
    知识分类。
    """

    ARCHITECTURE = "architecture"
    PRD = "prd"
    CODE_PATTERN = "code_pattern"
    BEST_PRACTICE = "best_practice"
    ISSUE = "issue"
    SOLUTION = "solution"
    DESIGN_DECISION = "design_decision"
    LESSON_LEARNED = "lesson_learned"
    EXPERIENCE = "experience"


class DocumentType(str, Enum):
    """
    文档类型（索引支持）。
    """

    MARKDOWN = "markdown"
    PDF = "pdf"
    CODE = "code"
    API = "api"
    ARCHITECTURE = "architecture"


class RetrievalMode(str, Enum):
    """
    检索模式。
    """

    KEYWORD = "keyword"
    EMBEDDING = "embedding"
    HYBRID = "hybrid"


class ExperienceType(str, Enum):
    """
    经验类型。
    """

    SUCCESS = "success"
    FAILURE = "failure"
    OPTIMIZATION = "optimization"


@dataclass
class KnowledgeEntry:
    """
    知识条目。
    """

    id: str
    title: str
    category: KnowledgeCategory
    content: str
    source_path: str = ""
    document_type: DocumentType = DocumentType.MARKDOWN
    tags: list[str] = field(default_factory=list)
    project_id: str = ""
    agent_name: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        title: str,
        category: KnowledgeCategory,
        content: str,
        source_path: str = "",
        document_type: DocumentType = DocumentType.MARKDOWN,
        tags: list[str] | None = None,
        project_id: str = "",
        agent_name: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeEntry:

        return cls(
            id=f"kb_{uuid4().hex[:12]}",
            title=title,
            category=category,
            content=content,
            source_path=source_path,
            document_type=document_type,
            tags=tags or [],
            project_id=project_id,
            agent_name=agent_name,
            metadata=metadata or {},
        )


@dataclass
class IndexRecord:
    """
    文档索引记录。
    """

    entry_id: str
    title: str
    category: str
    document_type: str
    source_path: str
    token_count: int = 0
    keywords: list[str] = field(default_factory=list)
    vector: dict[str, float] = field(default_factory=dict)


@dataclass
class RetrievalHit:
    """
    检索命中结果。
    """

    entry: KnowledgeEntry
    score: float
    match_type: str = ""
    snippet: str = ""

    @property
    def summary(self) -> str:

        path_hint = (
            f" path={self.entry.source_path}"
            if self.entry.source_path
            else ""
        )

        return (
            f"[{self.entry.category.value}] {self.entry.title}{path_hint} "
            f"(score={self.score:.2f}): {self.snippet[:120]}"
        )


@dataclass
class RetrievalResult:
    """
    检索结果。
    """

    success: bool
    query: str
    mode: RetrievalMode
    hits: list[RetrievalHit] = field(default_factory=list)
    error_message: str = ""

    @property
    def summary(self) -> str:

        if not self.hits:

            return f"Retrieval ({self.mode.value}): no results for '{self.query}'"

        lines = [
            f"Retrieval ({self.mode.value}): {len(self.hits)} hit(s)"
        ]

        for hit in self.hits[:5]:

            lines.append(f"- {hit.summary}")

        return "\n".join(lines)


@dataclass
class Recommendation:
    """
    单条知识推荐。
    """

    entry: KnowledgeEntry
    reason: str
    relevance: float = 0.0

    @property
    def summary(self) -> str:

        path_hint = (
            f" path={self.entry.source_path}"
            if self.entry.source_path
            else ""
        )

        return (
            f"[{self.entry.category.value}] {self.entry.title}{path_hint} "
            f"— {self.reason} (relevance={self.relevance:.2f})"
        )


@dataclass
class RecommendationResult:
    """
    推荐结果。
    """

    success: bool
    agent_name: str
    recommendations: list[Recommendation] = field(default_factory=list)
    error_message: str = ""

    @property
    def summary(self) -> str:

        if not self.recommendations:

            return f"Recommendations for {self.agent_name}: none"

        lines = [
            f"Recommendations for {self.agent_name}: "
            f"{len(self.recommendations)}"
        ]

        for rec in self.recommendations:

            lines.append(f"- {rec.summary}")

        return "\n".join(lines)


@dataclass
class ExperienceRecord:
    """
    经验记录。
    """

    id: str
    experience_type: ExperienceType
    title: str
    description: str
    agent_name: str = ""
    project_id: str = ""
    outcome: str = ""
    suggestions: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        experience_type: ExperienceType,
        title: str,
        description: str,
        agent_name: str = "",
        project_id: str = "",
        outcome: str = "",
        suggestions: list[str] | None = None,
    ) -> ExperienceRecord:

        return cls(
            id=f"exp_{uuid4().hex[:12]}",
            experience_type=experience_type,
            title=title,
            description=description,
            agent_name=agent_name,
            project_id=project_id,
            outcome=outcome,
            suggestions=suggestions or [],
        )


@dataclass
class LessonLearned:
    """
    经验教训记录。
    """

    id: str
    title: str
    situation: str
    lesson: str
    action: str
    category: str = ""
    project_id: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
    )

    @classmethod
    def create(
        cls,
        *,
        title: str,
        situation: str,
        lesson: str,
        action: str,
        category: str = "",
        project_id: str = "",
    ) -> LessonLearned:

        return cls(
            id=f"lesson_{uuid4().hex[:12]}",
            title=title,
            situation=situation,
            lesson=lesson,
            action=action,
            category=category,
            project_id=project_id,
        )


@dataclass
class KnowledgeContext:
    """
    知识上下文，供 PromptBuilder 注入。
    """

    retrieval_summary: str = ""
    recommendation_summary: str = ""
    best_practices: str = ""
    lessons_learned: str = ""
    historical_solutions: str = ""
    experience_summary: str = ""

    def to_shared_context(self) -> dict[str, str]:

        return {
            "knowledge_retrieval": self.retrieval_summary,
            "knowledge_recommendations": self.recommendation_summary,
            "knowledge_best_practices": self.best_practices,
            "knowledge_lessons_learned": self.lessons_learned,
            "knowledge_historical_solutions": self.historical_solutions,
            "knowledge_experience": self.experience_summary,
        }

    def to_prompt_block(self) -> str:

        return (
            f"## Retrieval\n{self.retrieval_summary or 'n/a'}\n\n"
            f"## Recommendations\n{self.recommendation_summary or 'none'}\n\n"
            f"## Best Practices\n{self.best_practices or 'n/a'}\n\n"
            f"## Lessons Learned\n{self.lessons_learned or 'none'}\n\n"
            f"## Historical Solutions\n"
            f"{self.historical_solutions or 'none'}\n\n"
            f"## Experience\n{self.experience_summary or 'n/a'}"
        )


@dataclass
class KnowledgePipelineResult:
    """
    知识流水线结果。
    """

    success: bool
    retrieval: RetrievalResult | None = None
    recommendations: RecommendationResult | None = None
    captured_count: int = 0
    lessons_count: int = 0
    context: KnowledgeContext = field(default_factory=KnowledgeContext)
    report_path: str = ""
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
