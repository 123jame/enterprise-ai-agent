from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.memory.manager import MemoryManager
from app.memory.types import MemoryRecord

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.knowledge.experience_manager import ExperienceManager
from applications.software_team.knowledge.knowledge_manager import KnowledgeManager
from applications.software_team.knowledge.knowledge_result import KnowledgeCategory
from applications.software_team.knowledge.knowledge_result import KnowledgeContext
from applications.software_team.knowledge.knowledge_result import KnowledgeEventType
from applications.software_team.knowledge.knowledge_result import KnowledgePipelineResult
from applications.software_team.knowledge.lesson_learned_manager import LessonLearnedManager
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.artifact import Artifact
from applications.software_team.project.models.project import Project


class KnowledgeService:
    """
    知识管理流水线编排：

    Knowledge Search → Recommendation → Agent → Knowledge Update →
    Experience / Lessons → Continuous Improvement
    """

    REPORT_DIR = "knowledge"
    REPORT_NAME = "KNOWLEDGE_REPORT.md"

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        knowledge_manager: KnowledgeManager | None = None,
        experience_manager: ExperienceManager | None = None,
        lesson_manager: LessonLearnedManager | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._knowledge = knowledge_manager or KnowledgeManager(
            settings=self._settings,
        )
        self._experience = experience_manager or self._knowledge.experience
        self._lessons = lesson_manager or self._knowledge.lessons

    @property
    def enabled(self) -> bool:

        return self._settings.enable_knowledge_management

    def initialize(
        self,
        project: Project,
        *,
        artifact_manager: ArtifactManager | None = None,
        memory_manager: MemoryManager | None = None,
        session_id: str = "",
    ) -> KnowledgePipelineResult:
        """
        项目启动时索引已有文档并采集知识。
        """

        if not self.enabled:

            return KnowledgePipelineResult(
                success=True,
                metadata={"skipped": True},
            )

        count = self._knowledge.index_project(project)

        captures = self._capture_workspace_artifacts(project)

        self._save_memory(
            memory_manager,
            session_id,
            KnowledgeEventType.CAPTURE,
            f"Indexed {count} records, captured {len(captures)} artifacts",
            {"indexed": count, "captured": len(captures)},
        )

        if artifact_manager is not None:

            self._register_capture_artifacts(
                artifact_manager,
                project,
                captures,
            )

        context = KnowledgeContext(
            retrieval_summary=f"Knowledge base initialized: {count} indexed",
        )

        return KnowledgePipelineResult(
            success=True,
            captured_count=len(captures),
            context=context,
            metadata={"indexed": count},
        )

    def prepare_for_agent(
        self,
        project: Project,
        *,
        agent_name: str,
        task: str = "",
        memory_manager: MemoryManager | None = None,
        session_id: str = "",
    ) -> KnowledgePipelineResult:
        """
        Agent 执行前：检索 + 推荐，构建 Knowledge Context。
        """

        if not self.enabled:

            return KnowledgePipelineResult(
                success=True,
                metadata={"skipped": True},
            )

        query = task or project.requirement

        retrieval = self._knowledge.search(project, query)
        recommendations = self._knowledge.recommend(
            project,
            agent_name=agent_name,
            task=task,
            query=query,
        )

        self._save_memory(
            memory_manager,
            session_id,
            KnowledgeEventType.RETRIEVAL,
            retrieval.summary,
            {"agent": agent_name, "hits": len(retrieval.hits)},
        )

        self._save_memory(
            memory_manager,
            session_id,
            KnowledgeEventType.RECOMMENDATION,
            recommendations.summary,
            {"agent": agent_name, "count": len(recommendations.recommendations)},
        )

        context = self._build_context(
            retrieval_summary=retrieval.summary,
            recommendation_summary=recommendations.summary,
            project=project,
            agent_name=agent_name,
        )

        return KnowledgePipelineResult(
            success=True,
            retrieval=retrieval,
            recommendations=recommendations,
            context=context,
            metadata={"agent": agent_name},
        )

    def update_after_agent(
        self,
        project: Project,
        *,
        agent_name: str,
        success: bool,
        summary: str = "",
        memory_manager: MemoryManager | None = None,
        session_id: str = "",
    ) -> KnowledgePipelineResult:
        """
        Agent 完成后：采集产物、沉淀经验。
        """

        if not self.enabled:

            return KnowledgePipelineResult(
                success=True,
                metadata={"skipped": True},
            )

        captured = self._capture_agent_artifacts(project, agent_name)
        lessons_count = 0

        if success:

            record = self._experience.capture_success(
                project,
                agent_name=agent_name,
                summary=summary or f"{agent_name} completed task",
            )

            self._save_memory(
                memory_manager,
                session_id,
                KnowledgeEventType.EXPERIENCE,
                record.title,
                {"type": "success", "agent": agent_name},
            )

        else:

            record = self._experience.capture_failure(
                project,
                agent_name=agent_name,
                summary=summary or f"{agent_name} failed",
            )

            lesson = self._lessons.record_from_failure(
                project,
                agent_name=agent_name,
                error_message=summary,
            )

            if lesson is not None:

                lessons_count = 1

                self._save_memory(
                    memory_manager,
                    session_id,
                    KnowledgeEventType.LESSON,
                    lesson.title,
                    {"agent": agent_name},
                )

            self._save_memory(
                memory_manager,
                session_id,
                KnowledgeEventType.EXPERIENCE,
                record.title,
                {"type": "failure", "agent": agent_name},
            )

        self._knowledge.index_project(project)

        return KnowledgePipelineResult(
            success=True,
            captured_count=len(captured),
            lessons_count=lessons_count,
            metadata={"agent": agent_name, "success": success},
        )

    def finalize(
        self,
        project: Project,
        *,
        artifact_manager: ArtifactManager,
        memory_manager: MemoryManager | None = None,
        session_id: str = "",
        pipeline_success: bool = True,
    ) -> KnowledgePipelineResult:
        """
        项目收尾：持续改进报告、经验与教训汇总。
        """

        if not self.enabled:

            return KnowledgePipelineResult(
                success=True,
                metadata={"skipped": True},
            )

        if not pipeline_success:

            self._lessons.record(
                project,
                title="Pipeline did not complete",
                situation="Software team pipeline failed",
                lesson="Incomplete delivery — review failed agent and retry",
                action="Analyze verification logs and re-run pipeline",
                category="pipeline_failure",
            )

        if pipeline_success:

            self._experience.capture_optimization(
                project,
                title="Project delivery completed",
                description=f"Project {project.name} delivered successfully",
                suggestions=[
                    "Archive knowledge entries for future reuse",
                    "Review lessons learned before next project",
                ],
            )

        experience_path = self._experience.write_report(
            project.workspace_path,
            project,
        )
        lessons_path = self._lessons.write_report(
            project.workspace_path,
            project,
        )
        report_path = self._write_knowledge_report(project)

        self._save_memory(
            memory_manager,
            session_id,
            KnowledgeEventType.IMPROVEMENT,
            f"Knowledge report: {report_path}",
            {"entries": self._knowledge.get_entry_count(project)},
        )

        context = self._build_context(
            project=project,
            include_history=True,
        )

        self._register_finalize_artifacts(
            artifact_manager,
            report_path=report_path,
            experience_path=experience_path,
            lessons_path=lessons_path,
        )

        return KnowledgePipelineResult(
            success=True,
            context=context,
            report_path=report_path,
            metadata={
                "entry_count": self._knowledge.get_entry_count(project),
            },
        )

    def build_context(
        self,
        project: Project,
        *,
        agent_name: str = "",
        task: str = "",
    ) -> KnowledgeContext:

        if not self.enabled:

            return KnowledgeContext()

        query = task or project.requirement
        retrieval = self._knowledge.search(project, query)

        recommendations = self._knowledge.recommend(
            project,
            agent_name=agent_name,
            task=task,
            query=query,
        ) if agent_name else None

        return self._build_context(
            retrieval_summary=retrieval.summary,
            recommendation_summary=(
                recommendations.summary if recommendations else ""
            ),
            project=project,
            agent_name=agent_name,
        )

    def _build_context(
        self,
        *,
        retrieval_summary: str = "",
        recommendation_summary: str = "",
        project: Project,
        agent_name: str = "",
        include_history: bool = False,
    ) -> KnowledgeContext:

        best_practices = recommendation_summary

        lessons = self._lessons.list_lessons(
            project.workspace_path,
            project_id=project.id,
        )
        lessons_text = "\n".join(
            f"- {l.title}: {l.lesson}"
            for l in lessons[-5:]
        ) or "none"

        experiences = self._experience.list_experiences(
            project.workspace_path,
            project_id=project.id,
        )
        experience_text = "\n".join(
            f"- [{e.experience_type.value}] {e.title}"
            for e in experiences[-5:]
        ) or "none"

        solutions = "\n".join(
            hit.summary
            for hit in (
                self._knowledge.search(
                    project,
                    "solution fix",
                ).hits[:3]
            )
        ) or "none"

        if include_history:

            retrieval_summary = (
                f"{retrieval_summary}\n"
                f"Total knowledge entries: "
                f"{self._knowledge.get_entry_count(project)}"
            )

        return KnowledgeContext(
            retrieval_summary=retrieval_summary,
            recommendation_summary=recommendation_summary,
            best_practices=best_practices,
            lessons_learned=lessons_text,
            historical_solutions=solutions,
            experience_summary=experience_text,
        )

    def _capture_workspace_artifacts(self, project: Project) -> list[str]:

        mappings = [
            ("docs/PRD.md", KnowledgeCategory.PRD, "ProductAgent"),
            ("docs/Architecture.md", KnowledgeCategory.ARCHITECTURE, "ArchitectAgent"),
            ("README.md", KnowledgeCategory.BEST_PRACTICE, "DocumentationAgent"),
        ]

        captured: list[str] = []

        for relative, category, agent in mappings:

            entry = self._knowledge.capture_from_file(
                project,
                file_path=relative,
                category=category,
                agent_name=agent,
            )

            if entry is not None:

                captured.append(entry.id)

        return captured

    def _capture_agent_artifacts(self, project: Project, agent_name: str) -> list[str]:

        mappings: dict[str, list[tuple[str, KnowledgeCategory]]] = {
            "ProductAgent": [("docs/PRD.md", KnowledgeCategory.PRD)],
            "ArchitectAgent": [
                ("docs/Architecture.md", KnowledgeCategory.ARCHITECTURE),
            ],
            "BackendAgent": [("backend/main.py", KnowledgeCategory.CODE_PATTERN)],
            "FrontendAgent": [
                ("frontend/package.json", KnowledgeCategory.CODE_PATTERN),
            ],
            "QAAgent": [("tests", KnowledgeCategory.SOLUTION)],
            "DocumentationAgent": [("README.md", KnowledgeCategory.BEST_PRACTICE)],
        }

        captured: list[str] = []

        for relative, category in mappings.get(agent_name, []):

            workspace = Path(project.workspace_path)
            path = workspace / relative

            if path.is_dir():

                for file_path in path.rglob("*"):

                    if file_path.is_file() and file_path.suffix in (
                        ".py", ".md", ".ts", ".js", ".json",
                    ):

                        entry = self._knowledge.capture_from_file(
                            project,
                            file_path=file_path,
                            category=category,
                            agent_name=agent_name,
                        )

                        if entry is not None:

                            captured.append(entry.id)

                continue

            entry = self._knowledge.capture_from_file(
                project,
                file_path=relative,
                category=category,
                agent_name=agent_name,
            )

            if entry is not None:

                captured.append(entry.id)

        return captured

    def _write_knowledge_report(self, project: Project) -> str:

        report_dir = Path(project.workspace_path) / self.REPORT_DIR
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / self.REPORT_NAME

        entries = self._knowledge.repository.list_entries(project.workspace_path)
        lessons = self._lessons.list_lessons(
            project.workspace_path,
            project_id=project.id,
        )
        experiences = self._experience.list_experiences(
            project.workspace_path,
            project_id=project.id,
        )

        content = f"""# Knowledge Report — {project.name}

## Summary
- Knowledge entries: {len(entries)}
- Lessons learned: {len(lessons)}
- Experiences: {len(experiences)}

## Categories
{self._category_breakdown(entries)}

## Continuous Improvement
- Reuse captured architecture patterns and PRD templates
- Apply lessons learned to avoid repeated failures
- Index grows automatically after each agent step

---
*Generated by KnowledgeService*
"""

        report_path.write_text(content, encoding=DEFAULT_ENCODING)

        return str(report_path)

    @staticmethod
    def _category_breakdown(entries) -> str:

        counts: dict[str, int] = {}

        for entry in entries:

            key = entry.category.value
            counts[key] = counts.get(key, 0) + 1

        return "\n".join(
            f"- {cat}: {count}"
            for cat, count in sorted(counts.items())
        ) or "- none"

    @staticmethod
    def _register_capture_artifacts(
        artifact_manager: ArtifactManager,
        project: Project,
        entry_ids: list[str],
    ) -> None:

        for entry_id in entry_ids:

            artifact_manager.register_knowledge_artifact(
                Artifact(
                    id=f"artifact_{uuid4().hex[:12]}",
                    name=f"knowledge_{entry_id}",
                    type="knowledge_report",
                    path=str(
                        Path(project.workspace_path)
                        / "knowledge"
                        / "entries"
                        / f"{entry_id}.json"
                    ),
                    owner="KnowledgeService",
                    metadata={"entry_id": entry_id, "stage": "capture"},
                )
            )

    @staticmethod
    def _register_finalize_artifacts(
        artifact_manager: ArtifactManager,
        *,
        report_path: str,
        experience_path: str,
        lessons_path: str,
    ) -> None:

        mappings = [
            (report_path, "KNOWLEDGE_REPORT.md", "knowledge_report"),
            (experience_path, "EXPERIENCE_LOG.md", "best_practice"),
            (lessons_path, "LESSONS_LEARNED.md", "lessons_learned"),
        ]

        for path, name, artifact_type in mappings:

            if not path:

                continue

            artifact_manager.register_knowledge_artifact(
                Artifact(
                    id=f"artifact_{uuid4().hex[:12]}",
                    name=name,
                    type=artifact_type,
                    path=path,
                    owner="KnowledgeService",
                    metadata={"stage": "finalize"},
                )
            )

    @staticmethod
    def _save_memory(
        memory_manager: MemoryManager | None,
        session_id: str,
        event_type: KnowledgeEventType,
        content: str,
        metadata: dict | None = None,
    ) -> None:

        if memory_manager is None or not session_id:

            return

        record = MemoryRecord(
            role="assistant",
            content=content,
            metadata={
                "type": "memory",
                "category": event_type.value,
                **(metadata or {}),
            },
        )

        memory_manager.memory.save(session_id, record)
