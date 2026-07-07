from dataclasses import dataclass
from dataclasses import field
from pathlib import Path


DEFAULT_SYSTEM_PROMPT_PATH = (
    Path(__file__)
    .resolve()
    .parent.parent
    / "prompts"
    / "system.txt"
)


@dataclass
class AgentConfig:
    """
    Agent Runtime 集中配置。
    """

    max_iterations: int = 5

    temperature: float | None = None

    tool_choice: str = "auto"

    system_prompt: str | None = None

    system_prompt_path: Path | None = field(
        default_factory=lambda: DEFAULT_SYSTEM_PROMPT_PATH
    )

    enable_rag: bool = False

    top_k: int = 3

    score_threshold: float = 0.0

    enable_mcp: bool = False

    mcp_servers: list[str] = field(
        default_factory=list
    )

    auto_discover_tools: bool = True

    auto_discover_resources: bool = True

    enable_mcp_prompts: bool = False

    mcp_prompt_name: str | None = None

    enable_planner: bool = False

    max_plan_steps: int = 10

    planner_model: str | None = None

    workflow_mode: str = "sequential"

    step_max_retries: int = 1

    enable_trace: bool = False

    enable_metrics: bool = False

    enable_evaluation: bool = False

    exporter_type: str = "console"

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """
        从环境变量/Settings 加载配置（预留扩展）。
        """

        return cls()
