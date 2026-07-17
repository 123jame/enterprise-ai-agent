from __future__ import annotations

from applications.platform.platform_result import AITeam
from applications.platform.platform_result import TeamType
from applications.platform.platform_store import PlatformStore
from applications.platform.settings import PlatformSettings


class TeamManager:
    """
    多 AI Team 管理：Software / QA / Research / Security。
    """

    STORE_KEY = "teams"

    _DEFAULT_AGENTS: dict[TeamType, list[str]] = {
        TeamType.SOFTWARE: [
            "ProductAgent",
            "ArchitectAgent",
            "BackendAgent",
            "FrontendAgent",
            "QAAgent",
            "DocumentationAgent",
        ],
        TeamType.QA: ["QAAgent"],
        TeamType.RESEARCH: ["ArchitectAgent", "DocumentationAgent"],
        TeamType.SECURITY: ["BackendAgent", "QAAgent"],
    }

    def __init__(
        self,
        settings: PlatformSettings | None = None,
        store: PlatformStore | None = None,
    ):

        self._settings = settings or PlatformSettings()
        self._store = store or PlatformStore(settings=self._settings)

    def create(
        self,
        *,
        name: str,
        team_type: TeamType,
        organization_id: str,
        agent_names: list[str] | None = None,
    ) -> AITeam:

        agents = agent_names or self._DEFAULT_AGENTS.get(team_type, [])

        team = AITeam.create(
            name=name,
            team_type=team_type,
            organization_id=organization_id,
            agent_names=agents,
        )

        self._store.append(self.STORE_KEY, self._to_dict(team))

        return team

    def get(self, team_id: str) -> AITeam | None:

        data = self._store.find(self.STORE_KEY, team_id)

        if data is None:

            return None

        return self._from_dict(data)

    def get_by_type(
        self,
        organization_id: str,
        team_type: TeamType,
    ) -> AITeam | None:

        for item in self._store.filter(
            self.STORE_KEY,
            organization_id=organization_id,
            team_type=team_type.value,
        ):

            return self._from_dict(item)

        return None

    def get_or_create_default(
        self,
        organization_id: str,
        team_type: TeamType = TeamType.SOFTWARE,
    ) -> AITeam:

        existing = self.get_by_type(organization_id, team_type)

        if existing is not None:

            return existing

        return self.create(
            name=f"{team_type.value.replace('_', ' ').title()}",
            team_type=team_type,
            organization_id=organization_id,
        )

    def list_by_organization(
        self,
        organization_id: str,
    ) -> list[AITeam]:

        return [
            self._from_dict(item)
            for item in self._store.filter(
                self.STORE_KEY,
                organization_id=organization_id,
            )
        ]

    @staticmethod
    def summarize(team: AITeam) -> str:

        return (
            f"{team.name} ({team.team_type.value}, id={team.id})\n"
            f"Agents: {', '.join(team.agent_names) or 'none'}\n"
            f"Enabled: {team.enabled}"
        )

    @staticmethod
    def _to_dict(team: AITeam) -> dict:

        return {
            "id": team.id,
            "name": team.name,
            "team_type": team.team_type.value,
            "organization_id": team.organization_id,
            "agent_names": team.agent_names,
            "enabled": team.enabled,
            "metadata": team.metadata,
        }

    @staticmethod
    def _from_dict(data: dict) -> AITeam:

        return AITeam(
            id=data["id"],
            name=data["name"],
            team_type=TeamType(data["team_type"]),
            organization_id=data["organization_id"],
            agent_names=data.get("agent_names", []),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )
