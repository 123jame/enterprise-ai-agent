from __future__ import annotations

import re

from applications.software_team.config.settings import SoftwareTeamSettings


class BranchStrategy:
    """
    Git 分支命名与创建策略。

    支持：main / develop / feature/* / bugfix/* / release/*
    """

    MAIN = "main"
    DEVELOP = "develop"

    _AGENT_SLUGS: dict[str, str] = {
        "ProductAgent": "product-prd",
        "ArchitectAgent": "architecture",
        "BackendAgent": "backend",
        "FrontendAgent": "frontend",
        "QAAgent": "qa-tests",
        "DocumentationAgent": "documentation",
    }

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()

    @property
    def main_branch(self) -> str:

        return self._settings.git_default_branch or self.MAIN

    @property
    def develop_branch(self) -> str:

        return self._settings.git_develop_branch or self.DEVELOP

    def feature_branch(
        self,
        agent_name: str,
        *,
        project_name: str | None = None,
    ) -> str:

        slug = self._AGENT_SLUGS.get(
            agent_name,
            self._slugify(agent_name),
        )

        if project_name:

            prefix = self._slugify(project_name)[:20]

            return f"feature/{prefix}-{slug}"

        return f"feature/{slug}"

    def bugfix_branch(
        self,
        name: str,
    ) -> str:

        return f"bugfix/{self._slugify(name)}"

    def release_branch(
        self,
        version: str,
    ) -> str:

        return f"release/{self._slugify(version)}"

    def agent_slug(
        self,
        agent_name: str,
    ) -> str:

        return self._AGENT_SLUGS.get(
            agent_name,
            self._slugify(agent_name),
        )

    @staticmethod
    def _slugify(value: str) -> str:

        text = value.strip().lower()
        text = re.sub(r"[^a-z0-9]+", "-", text)

        return text.strip("-") or "branch"
