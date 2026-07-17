from __future__ import annotations

from pathlib import Path

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.knowledge.knowledge_repository import KnowledgeRepository
from applications.software_team.knowledge.knowledge_result import KnowledgeCategory
from applications.software_team.knowledge.knowledge_result import KnowledgeEntry
from applications.software_team.knowledge.knowledge_result import Recommendation
from applications.software_team.knowledge.knowledge_result import RecommendationResult
from applications.software_team.knowledge.knowledge_result import RetrievalHit
from applications.software_team.project.models.project import Project


class RecommendationManager:
    """
    根据当前任务、Agent、项目推荐最佳实践、历史方案、相似项目。
    """

    _AGENT_CATEGORIES: dict[str, list[KnowledgeCategory]] = {
        "ProductAgent": [
            KnowledgeCategory.PRD,
            KnowledgeCategory.BEST_PRACTICE,
            KnowledgeCategory.DESIGN_DECISION,
        ],
        "ArchitectAgent": [
            KnowledgeCategory.ARCHITECTURE,
            KnowledgeCategory.DESIGN_DECISION,
            KnowledgeCategory.BEST_PRACTICE,
        ],
        "BackendAgent": [
            KnowledgeCategory.CODE_PATTERN,
            KnowledgeCategory.SOLUTION,
            KnowledgeCategory.ARCHITECTURE,
        ],
        "FrontendAgent": [
            KnowledgeCategory.CODE_PATTERN,
            KnowledgeCategory.BEST_PRACTICE,
            KnowledgeCategory.ARCHITECTURE,
        ],
        "QAAgent": [
            KnowledgeCategory.ISSUE,
            KnowledgeCategory.SOLUTION,
            KnowledgeCategory.BEST_PRACTICE,
        ],
        "DocumentationAgent": [
            KnowledgeCategory.BEST_PRACTICE,
            KnowledgeCategory.ARCHITECTURE,
            KnowledgeCategory.PRD,
        ],
    }

    _DEFAULT_PRACTICES: dict[str, list[str]] = {
        "ProductAgent": [
            "PRD 应包含用户故事、功能列表与验收标准",
            "需求描述应具体、可测试、无歧义",
        ],
        "ArchitectAgent": [
            "架构文档应描述模块边界与数据流",
            "优先选择团队熟悉的技术栈",
        ],
        "BackendAgent": [
            "FastAPI 项目使用 main.py + requirements.txt 结构",
            "API 路由应有 /api/health 健康检查端点",
        ],
        "FrontendAgent": [
            "前端项目使用 package.json 管理依赖",
            "组件化设计，保持 UI 与 API 解耦",
        ],
        "QAAgent": [
            "测试覆盖核心 API 与关键用户路径",
            "使用 pytest 组织后端测试",
        ],
        "DocumentationAgent": [
            "README 应包含安装、运行与部署说明",
            "文档与代码保持同步更新",
        ],
    }

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        repository: KnowledgeRepository | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._repo = repository or KnowledgeRepository(settings=self._settings)

    def recommend(
        self,
        project: Project,
        *,
        agent_name: str,
        task: str = "",
        retrieval_hits: list[RetrievalHit] | None = None,
    ) -> RecommendationResult:

        workspace = project.workspace_path
        max_items = self._settings.knowledge_max_recommendations

        recommendations: list[Recommendation] = []
        categories = self._AGENT_CATEGORIES.get(agent_name, [])

        entries = self._repo.list_entries(workspace)

        for entry in entries:

            if categories and entry.category not in categories:

                continue

            relevance = self._score_entry(entry, agent_name, task, project)

            if relevance <= 0:

                continue

            recommendations.append(
                Recommendation(
                    entry=entry,
                    reason=f"Relevant {entry.category.value} for {agent_name}",
                    relevance=relevance,
                )
            )

        if retrieval_hits:

            for hit in retrieval_hits:

                if any(
                    r.entry.id == hit.entry.id
                    for r in recommendations
                ):

                    continue

                recommendations.append(
                    Recommendation(
                        entry=hit.entry,
                        reason=f"Retrieved match for '{task[:40]}'",
                        relevance=hit.score,
                    )
                )

        for practice in self._DEFAULT_PRACTICES.get(agent_name, []):

            entry = KnowledgeEntry.create(
                title=f"Best Practice: {agent_name}",
                category=KnowledgeCategory.BEST_PRACTICE,
                content=practice,
                agent_name=agent_name,
                project_id=project.id,
            )

            recommendations.append(
                Recommendation(
                    entry=entry,
                    reason="Built-in best practice",
                    relevance=0.5,
                )
            )

        recommendations.sort(key=lambda r: r.relevance, reverse=True)
        recommendations = recommendations[:max_items]

        return RecommendationResult(
            success=True,
            agent_name=agent_name,
            recommendations=recommendations,
        )

    @staticmethod
    def _score_entry(
        entry: KnowledgeEntry,
        agent_name: str,
        task: str,
        project: Project,
    ) -> float:

        score = 0.0

        if entry.agent_name == agent_name:

            score += 0.4

        if entry.project_id == project.id:

            score += 0.3

        task_lower = task.lower()

        if task_lower and task_lower in entry.content.lower():

            score += 0.3

        if task_lower and task_lower in entry.title.lower():

            score += 0.2

        return min(score, 1.0)
