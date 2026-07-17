from __future__ import annotations

from pathlib import Path

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.knowledge.knowledge_repository import KnowledgeRepository
from applications.software_team.knowledge.knowledge_result import ExperienceRecord
from applications.software_team.knowledge.knowledge_result import ExperienceType
from applications.software_team.knowledge.knowledge_result import KnowledgeCategory
from applications.software_team.knowledge.knowledge_result import KnowledgeEntry
from applications.software_team.project.models.project import Project


class ExperienceManager:
    """
    沉淀成功经验、失败经验、优化建议。
    """

    REPORT_NAME = "EXPERIENCE_LOG.md"

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        repository: KnowledgeRepository | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._repo = repository or KnowledgeRepository(settings=self._settings)

    def capture_success(
        self,
        project: Project,
        *,
        agent_name: str,
        summary: str,
        suggestions: list[str] | None = None,
    ) -> ExperienceRecord:

        record = ExperienceRecord.create(
            experience_type=ExperienceType.SUCCESS,
            title=f"{agent_name} completed successfully",
            description=summary,
            agent_name=agent_name,
            project_id=project.id,
            outcome="success",
            suggestions=suggestions or [],
        )

        self._persist(project.workspace_path, record)

        return record

    def capture_failure(
        self,
        project: Project,
        *,
        agent_name: str,
        summary: str,
        suggestions: list[str] | None = None,
    ) -> ExperienceRecord:

        record = ExperienceRecord.create(
            experience_type=ExperienceType.FAILURE,
            title=f"{agent_name} encountered failure",
            description=summary,
            agent_name=agent_name,
            project_id=project.id,
            outcome="failure",
            suggestions=suggestions or [
                "Review error logs and retry with fix instruction",
                "Check artifact dependencies before re-running agent",
            ],
        )

        self._persist(project.workspace_path, record)

        return record

    def capture_optimization(
        self,
        project: Project,
        *,
        title: str,
        description: str,
        suggestions: list[str] | None = None,
    ) -> ExperienceRecord:

        record = ExperienceRecord.create(
            experience_type=ExperienceType.OPTIMIZATION,
            title=title,
            description=description,
            project_id=project.id,
            outcome="improvement",
            suggestions=suggestions or [],
        )

        self._persist(project.workspace_path, record)

        return record

    def list_experiences(
        self,
        workspace: str | Path,
        *,
        project_id: str = "",
        experience_type: ExperienceType | None = None,
    ) -> list[ExperienceRecord]:

        entries = self._repo.list_entries(
            workspace,
            category=KnowledgeCategory.EXPERIENCE,
            project_id=project_id,
        )

        records: list[ExperienceRecord] = []

        for entry in entries:

            exp_type = ExperienceType(
                entry.metadata.get(
                    "experience_type",
                    ExperienceType.SUCCESS.value,
                )
            )

            if experience_type is not None and exp_type != experience_type:

                continue

            records.append(
                ExperienceRecord(
                    id=entry.id,
                    experience_type=exp_type,
                    title=entry.title,
                    description=entry.content,
                    agent_name=entry.agent_name,
                    project_id=entry.project_id,
                    outcome=entry.metadata.get("outcome", ""),
                    suggestions=entry.metadata.get("suggestions", []),
                    created_at=entry.created_at,
                    metadata=entry.metadata,
                )
            )

        return records

    def write_report(
        self,
        workspace: str | Path,
        project: Project,
    ) -> str:

        records = self.list_experiences(
            workspace,
            project_id=project.id,
        )

        report_dir = Path(workspace) / "knowledge"
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / self.REPORT_NAME

        lines = [
            f"# Experience Log — {project.name}",
            "",
            f"Total experiences: {len(records)}",
            "",
        ]

        for record in records:

            lines.append(
                f"## [{record.experience_type.value}] {record.title}\n"
                f"{record.description}\n"
                f"Suggestions: {', '.join(record.suggestions) or 'n/a'}\n"
            )

        report_path.write_text("\n".join(lines), encoding=DEFAULT_ENCODING)

        return str(report_path)

    def _persist(
        self,
        workspace: str | Path,
        record: ExperienceRecord,
    ) -> KnowledgeEntry:

        entry = KnowledgeEntry.create(
            title=record.title,
            category=KnowledgeCategory.EXPERIENCE,
            content=record.description,
            agent_name=record.agent_name,
            project_id=record.project_id,
            tags=[record.experience_type.value],
            metadata={
                "experience_type": record.experience_type.value,
                "outcome": record.outcome,
                "suggestions": record.suggestions,
            },
        )

        self._repo.save(workspace, entry)

        return entry
