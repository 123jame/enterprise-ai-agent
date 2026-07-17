from __future__ import annotations

from pathlib import Path

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.knowledge.knowledge_repository import KnowledgeRepository
from applications.software_team.knowledge.knowledge_result import KnowledgeCategory
from applications.software_team.knowledge.knowledge_result import KnowledgeEntry
from applications.software_team.knowledge.knowledge_result import LessonLearned
from applications.software_team.project.models.project import Project


class LessonLearnedManager:
    """
    记录 Lessons Learned，避免重复犯错。
    """

    REPORT_NAME = "LESSONS_LEARNED.md"

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        repository: KnowledgeRepository | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._repo = repository or KnowledgeRepository(settings=self._settings)

    def record(
        self,
        project: Project,
        *,
        title: str,
        situation: str,
        lesson: str,
        action: str,
        category: str = "",
    ) -> LessonLearned:

        item = LessonLearned.create(
            title=title,
            situation=situation,
            lesson=lesson,
            action=action,
            category=category,
            project_id=project.id,
        )

        entry = KnowledgeEntry.create(
            title=item.title,
            category=KnowledgeCategory.LESSON_LEARNED,
            content=(
                f"Situation: {item.situation}\n\n"
                f"Lesson: {item.lesson}\n\n"
                f"Action: {item.action}"
            ),
            project_id=project.id,
            tags=[category] if category else [],
            metadata={
                "situation": item.situation,
                "lesson": item.lesson,
                "action": item.action,
                "category": category,
            },
        )

        entry.id = item.id
        self._repo.save(project.workspace_path, entry)

        return item

    def record_from_failure(
        self,
        project: Project,
        *,
        agent_name: str,
        error_message: str,
    ) -> LessonLearned | None:

        if not error_message:

            return None

        return self.record(
            project,
            title=f"Failure in {agent_name}",
            situation=error_message[:500],
            lesson=f"Agent {agent_name} failed — review dependencies and output quality",
            action="Re-run with verification feedback and fix instruction",
            category="agent_failure",
        )

    def list_lessons(
        self,
        workspace: str | Path,
        *,
        project_id: str = "",
    ) -> list[LessonLearned]:

        entries = self._repo.list_entries(
            workspace,
            category=KnowledgeCategory.LESSON_LEARNED,
            project_id=project_id,
        )

        lessons: list[LessonLearned] = []

        for entry in entries:

            lessons.append(
                LessonLearned(
                    id=entry.id,
                    title=entry.title,
                    situation=entry.metadata.get("situation", ""),
                    lesson=entry.metadata.get("lesson", ""),
                    action=entry.metadata.get("action", ""),
                    category=entry.metadata.get("category", ""),
                    project_id=entry.project_id,
                    created_at=entry.created_at,
                )
            )

        return lessons

    def write_report(
        self,
        workspace: str | Path,
        project: Project,
    ) -> str:

        lessons = self.list_lessons(
            workspace,
            project_id=project.id,
        )

        report_dir = Path(workspace) / "knowledge"
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / self.REPORT_NAME

        lines = [
            f"# Lessons Learned — {project.name}",
            "",
            f"Total lessons: {len(lessons)}",
            "",
        ]

        for lesson in lessons:

            lines.extend([
                f"## {lesson.title}",
                f"**Situation:** {lesson.situation}",
                f"**Lesson:** {lesson.lesson}",
                f"**Action:** {lesson.action}",
                "",
            ])

        report_path.write_text("\n".join(lines), encoding=DEFAULT_ENCODING)

        return str(report_path)
