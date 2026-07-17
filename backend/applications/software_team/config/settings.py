from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class SoftwareTeamSettings(BaseSettings):
    """
    AI Software Team 配置。
    """

    model_config = SettingsConfigDict(
        env_prefix="SOFTWARE_TEAM_",
    )

    workspace_root: Path = Field(
        default=Path("workspace"),
        description="项目工作空间根目录",
    )

    max_agents: int = Field(
        default=10,
        description="最大 Agent 数量",
    )

    default_language: str = Field(
        default="python",
        description="默认开发语言",
    )

    max_loop_iterations: int = Field(
        default=16,
        description="Agent Loop 最大迭代次数",
    )

    enable_rag: bool = Field(
        default=False,
        description="是否启用 RAG",
    )

    enable_mcp_tools: bool = Field(
        default=False,
        description="是否启用 MCP Tool",
    )

    enable_trace: bool = Field(
        default=False,
        description="是否启用 Trace",
    )

    enable_template_fallback: bool = Field(
        default=True,
        description="LLM 失败时是否回退到模板生成",
    )

    execution_timeout_seconds: int = Field(
        default=120,
        description="代码执行超时（秒）",
    )

    execution_install_dependencies: bool = Field(
        default=False,
        description="执行前是否安装依赖（pip/npm）",
    )

    max_verification_retries: int = Field(
        default=3,
        description="验证失败最大重试次数",
    )

    enable_pytest: bool = Field(
        default=True,
        description="验证时是否运行 pytest",
    )

    enable_type_check: bool = Field(
        default=False,
        description="验证时是否运行 mypy 类型检查",
    )

    enable_verification: bool = Field(
        default=True,
        description="Pipeline 是否在 Agent 生成后执行验证",
    )

    enable_git: bool = Field(
        default=True,
        description="是否启用 Git 协作",
    )

    git_default_branch: str = Field(
        default="main",
        description="Git 默认主分支",
    )

    git_develop_branch: str = Field(
        default="develop",
        description="Git 开发集成分支",
    )

    git_auto_merge_to_develop: bool = Field(
        default=True,
        description="每个 Agent 完成后是否 merge 到 develop",
    )

    git_finalize_to_main: bool = Field(
        default=True,
        description="Pipeline 完成后是否 merge develop 到 main",
    )

    enable_deployment: bool = Field(
        default=True,
        description="Pipeline 完成后是否执行 DevOps 部署",
    )

    deployment_mode: str = Field(
        default="local",
        description="部署模式：local / docker / remote",
    )

    deployment_timeout_seconds: int = Field(
        default=300,
        description="部署操作超时（秒）",
    )

    deployment_install_dependencies: bool = Field(
        default=False,
        description="构建时是否安装依赖",
    )

    deployment_run_docker: bool = Field(
        default=False,
        description="是否实际运行 docker compose up",
    )

    deployment_health_port: int = Field(
        default=8000,
        description="健康检查端口",
    )

    deployment_health_http: bool = Field(
        default=False,
        description="是否执行 HTTP 健康检查",
    )

    deployment_health_timeout: int = Field(
        default=5,
        description="HTTP 健康检查超时（秒）",
    )

    deployment_version: str = Field(
        default="",
        description="固定发布版本号（空则自动生成）",
    )

    enable_operations: bool = Field(
        default=True,
        description="是否启用运维监控流水线",
    )

    operations_auto_fix: bool = Field(
        default=False,
        description="告警后是否自动调度 Agent 修复",
    )

    operations_auto_redeploy: bool = Field(
        default=True,
        description="Auto Fix 验证通过后是否自动 Redeploy",
    )

    operations_after_deploy: bool = Field(
        default=False,
        description="Pipeline 部署完成后是否执行一次运维巡检",
    )

    operations_monitor_http: bool = Field(
        default=False,
        description="是否执行 HTTP API 监控",
    )

    operations_timeout_seconds: int = Field(
        default=60,
        description="运维命令超时（秒）",
    )

    operations_alert_error_rate: float = Field(
        default=0.25,
        description="错误率告警阈值（0-1）",
    )

    operations_alert_response_time_ms: int = Field(
        default=3000,
        description="响应时间告警阈值（毫秒）",
    )

    operations_cpu_threshold_percent: float = Field(
        default=90.0,
        description="CPU 使用率告警阈值",
    )

    operations_memory_threshold_percent: float = Field(
        default=90.0,
        description="内存使用率告警阈值",
    )

    operations_disk_threshold_percent: float = Field(
        default=95.0,
        description="磁盘使用率告警阈值",
    )

    operations_max_fix_tasks: int = Field(
        default=2,
        description="单次运维最多执行的修复任务数",
    )

    enable_project_management: bool = Field(
        default=True,
        description="是否启用项目管理流水线",
    )

    management_sprint_days: int = Field(
        default=14,
        description="默认 Sprint 周期（天）",
    )

    management_task_overload_threshold: int = Field(
        default=2,
        description="Agent 任务超负荷阈值",
    )

    management_risk_auto_assess: bool = Field(
        default=True,
        description="是否在项目收尾自动风险评估",
    )

    enable_knowledge_management: bool = Field(
        default=True,
        description="是否启用知识管理与持续改进",
    )

    knowledge_auto_capture: bool = Field(
        default=True,
        description="是否自动采集 Agent 产物到知识库",
    )

    knowledge_retrieval_mode: str = Field(
        default="hybrid",
        description="检索模式：keyword / embedding / hybrid",
    )

    knowledge_max_recommendations: int = Field(
        default=5,
        description="每次推荐的最大知识条目数",
    )

    knowledge_max_retrieval_results: int = Field(
        default=10,
        description="每次检索的最大结果数",
    )
