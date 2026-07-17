from __future__ import annotations

from applications.software_team.project.models.artifact import Artifact
from applications.software_team.project.models.project import Project


class CommitMessageBuilder:
    """
    根据 Agent / Artifact / Project 生成规范 Commit Message。

    遵循 Conventional Commits 风格。
    """

    _AGENT_COMMIT_TYPE: dict[str, str] = {
        "ProductAgent": "docs",
        "ArchitectAgent": "docs",
        "BackendAgent": "feat",
        "FrontendAgent": "feat",
        "QAAgent": "test",
        "DocumentationAgent": "docs",
    }

    _AGENT_SCOPE: dict[str, str] = {
        "ProductAgent": "prd",
        "ArchitectAgent": "architecture",
        "BackendAgent": "backend",
        "FrontendAgent": "frontend",
        "QAAgent": "tests",
        "DocumentationAgent": "readme",
    }

    _AGENT_SUMMARY: dict[str, str] = {
        "ProductAgent": "add product requirements document",
        "ArchitectAgent": "add system architecture document",
        "BackendAgent": "implement backend project skeleton",
        "FrontendAgent": "implement frontend project skeleton",
        "QAAgent": "add test suite",
        "DocumentationAgent": "update project README",
    }

    def build(
        self,
        *,
        agent_name: str,
        project: Project,
        artifacts: list[Artifact],
        changed_summary: str = "",
    ) -> str:
        """
        生成 commit message，例如：
        feat(backend): implement backend project skeleton
        """

        commit_type = self._AGENT_COMMIT_TYPE.get(
            agent_name,
            "chore",
        )

        scope = self._AGENT_SCOPE.get(
            agent_name,
            self._slug_scope(agent_name),
        )

        summary = self._AGENT_SUMMARY.get(
            agent_name,
            f"update artifacts for {agent_name}",
        )

        body_lines = [
            f"Project: {project.name}",
            f"Agent: {agent_name}",
        ]

        if artifacts:

            body_lines.append("Artifacts:")

            for artifact in artifacts:

                body_lines.append(
                    f"- {artifact.name} ({artifact.type})"
                )

        if changed_summary:

            body_lines.append("")
            body_lines.append("Changes:")
            body_lines.append(changed_summary[:1000])

        header = f"{commit_type}({scope}): {summary}"

        return header + "\n\n" + "\n".join(body_lines)

    @staticmethod
    def _slug_scope(
        agent_name: str,
    ) -> str:

        return (
            agent_name.replace("Agent", "")
            .lower()
            or "team"
        )
