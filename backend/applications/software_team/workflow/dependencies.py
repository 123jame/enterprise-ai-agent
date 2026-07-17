from __future__ import annotations

from dataclasses import dataclass

from applications.software_team.project.models.project_status import ProjectStatus


@dataclass(frozen=True)
class PipelineStep:
    """
    流水线中的单个 Agent 步骤。
    """

    agent_name: str

    status: ProjectStatus

    task: str = ""


# 标准软件开发流水线（顺序固定）
DEFAULT_PIPELINE: tuple[PipelineStep, ...] = (
    PipelineStep(
        agent_name="ProductAgent",
        status=ProjectStatus.PLANNING,
        task="生成产品需求文档 PRD.md",
    ),
    PipelineStep(
        agent_name="ArchitectAgent",
        status=ProjectStatus.DESIGNING,
        task="生成系统架构文档 Architecture.md",
    ),
    PipelineStep(
        agent_name="BackendAgent",
        status=ProjectStatus.DEVELOPING,
        task="生成后端代码 backend/",
    ),
    PipelineStep(
        agent_name="FrontendAgent",
        status=ProjectStatus.DEVELOPING,
        task="生成前端代码 frontend/",
    ),
    PipelineStep(
        agent_name="QAAgent",
        status=ProjectStatus.TESTING,
        task="生成测试代码 tests/",
    ),
    PipelineStep(
        agent_name="DocumentationAgent",
        status=ProjectStatus.DELIVERING,
        task="生成项目文档 README.md",
    ),
)


class AgentDependencyRegistry:
    """
    统一 Agent 产物依赖关系。

    Agent 不互相引用，仅通过 ArtifactManager + 本注册表声明依赖。
    """

    # 依赖项：文件名、目录名或 "*"（全部产物）
    _DEPENDENCIES: dict[str, tuple[str, ...]] = {
        "ProductAgent": (),
        "ArchitectAgent": ("PRD.md",),
        "BackendAgent": ("Architecture.md",),
        "FrontendAgent": ("Architecture.md",),
        "QAAgent": ("backend", "frontend"),
        "DocumentationAgent": ("*",),
    }

    _ROLES: dict[str, str] = {
        "ProductAgent": "product_manager",
        "ArchitectAgent": "software_architect",
        "BackendAgent": "backend_engineer",
        "FrontendAgent": "frontend_engineer",
        "QAAgent": "qa_engineer",
        "DocumentationAgent": "technical_writer",
    }

    _ROLE_PROMPTS: dict[str, str] = {
        "ProductAgent": (
            "你是一名资深产品经理，负责编写清晰、可执行的 PRD。"
        ),
        "ArchitectAgent": (
            "你是一名软件架构师，负责基于 PRD 设计系统架构。"
        ),
        "BackendAgent": (
            "你是一名后端工程师，负责基于架构文档实现后端 API。"
        ),
        "FrontendAgent": (
            "你是一名前端工程师，负责基于架构文档实现前端界面。"
        ),
        "QAAgent": (
            "你是一名 QA 工程师，负责编写测试用例并验证前后端代码。"
        ),
        "DocumentationAgent": (
            "你是一名技术文档工程师，负责汇总全部产物并编写 README。"
        ),
    }

    def get_dependencies(
        self,
        agent_name: str,
    ) -> tuple[str, ...]:

        return self._DEPENDENCIES.get(agent_name, ())

    def get_role(self, agent_name: str) -> str:

        return self._ROLES.get(agent_name, "engineer")

    def get_role_prompt(self, agent_name: str) -> str:

        return self._ROLE_PROMPTS.get(
            agent_name,
            "你是一名软件工程师。",
        )

    def get_pipeline(self) -> tuple[PipelineStep, ...]:

        return DEFAULT_PIPELINE

    _TASK_INSTRUCTIONS: dict[str, str] = {
        "ProductAgent": (
            "请根据用户需求编写精简版 PRD，并写入 docs/PRD.md（仅调用一次 write_file）。"
            "要求：Markdown 不超过 3500 字；禁止使用 emoji；"
            "包含项目概述、用户角色、核心功能列表、非功能需求、技术栈、验收标准即可。"
            "若 docs/PRD.md 已存在且内容完整，不要重复写入，直接总结完成。"
            "路径均相对于 Workspace 根目录，不要加 workspace/ 前缀。"
            "完成后用简短文字确认，不要再次调用 write_file。"
        ),
        "ArchitectAgent": (
            "请阅读 PRD，设计系统架构并生成 Architecture.md。"
            "使用 write_file 工具将 Markdown 写入 docs/Architecture.md。"
            "路径均相对于 Workspace 根目录。"
            "完成后直接输出架构文档全文作为最终答案。"
        ),
        "BackendAgent": (
            "请根据 Architecture 文档，生成可运行的 FastAPI 后端项目骨架。"
            "使用 write_file 工具将代码写入 backend/ 目录（如 backend/main.py）。"
            "至少包含 main.py 与 requirements.txt。"
            "路径均相对于 Workspace 根目录。"
            "完成后总结已创建的文件列表。"
        ),
        "FrontendAgent": (
            "请根据 Architecture 文档，生成可运行的前端项目骨架。"
            "使用 write_file 工具将代码写入 frontend/ 目录。"
            "路径均相对于 Workspace 根目录。"
            "完成后总结已创建的文件列表。"
        ),
        "QAAgent": (
            "请根据 backend/ 与 frontend/ 代码，生成可运行的 pytest 测试。"
            "使用 write_file 工具将测试写入 tests/ 目录。"
            "优先编写简单 smoke test（如 test_health.py），避免复杂 conftest；"
            "若使用 SQLAlchemy 2.x，请用 connection.execute()，"
            "不要使用已废弃的 engine.execute()；"
            "在 workspace 根目录创建 requirements.txt（含 pytest、httpx、fastapi 等）。"
            "路径均相对于 Workspace 根目录。"
            "完成后总结测试覆盖范围。"
        ),
        "DocumentationAgent": (
            "请汇总全部产物，生成完整 README.md。"
            "使用 write_file 工具写入 README.md。"
            "路径均相对于 Workspace 根目录。"
            "完成后直接输出 README 全文作为最终答案。"
        ),
    }

    def get_task_instruction(
        self,
        agent_name: str,
    ) -> str:

        return self._TASK_INSTRUCTIONS.get(
            agent_name,
            "请完成当前阶段的软件开发任务。",
        )

    _VERIFICATION_TARGETS: dict[str, str] = {
        "ProductAgent": "docs/PRD.md",
        "ArchitectAgent": "docs/Architecture.md",
        "BackendAgent": "backend",
        "FrontendAgent": "frontend",
        "QAAgent": "tests",
        "DocumentationAgent": "README.md",
    }

    def get_verification_target(
        self,
        agent_name: str,
    ) -> str | None:

        return self._VERIFICATION_TARGETS.get(agent_name)

    def is_verifiable(
        self,
        agent_name: str,
    ) -> bool:

        return agent_name in self._VERIFICATION_TARGETS
