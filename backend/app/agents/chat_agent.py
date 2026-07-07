from app.agents.base_agent import BaseAgent
from app.agents.types import AgentContext
from app.agents.types import AgentResult

from app.llm.factory import get_llm_client

from app.memory.exceptions import MemoryError

from app.mcp.client.local import LocalMCPClient
from app.mcp.server_manager import MCPServerManager

from app.observability.collector import TraceCollector
from app.observability.evaluation import Evaluator
from app.observability.evaluation import RuleBasedEvaluator
from app.observability.exporter import create_trace_exporter
from app.observability.metrics import MetricsCollector
from app.observability.player import TracePlayer

from app.multi_agent.agent import Agent
from app.runtime.agent_executor import AgentExecutor
from app.runtime.config import AgentConfig
from app.runtime.error_handler import AgentErrorHandler
from app.runtime.observation_builder import ObservationBuilder
from app.runtime.plan.error_handler import WorkflowErrorHandler
from app.runtime.plan.llm_planner import LLMPlanner
from app.runtime.plan.planner import NoPlanner
from app.runtime.plan.planner import Planner
from app.runtime.plan.step_executor import StepExecutor
from app.runtime.plan.workflow import SequentialWorkflow
from app.runtime.plan.workflow_executor import WorkflowExecutor
from app.runtime.prompt_builder import PromptBuilder
from app.runtime.tool_message_builder import ToolMessageBuilder
from app.runtime.tracer import AgentTracer

from app.tools.manager import ToolManager


class ChatAgent(BaseAgent, Agent):
    """
    对话 Agent。

    支持 Plan-and-Execute：Planner → WorkflowExecutor → Agent Loop。
    enable_planner=False 时保持原有 ReAct 行为。
    enable_trace=True 时接入 TraceCollector，完整记录执行过程。

    同时实现 Multi-Agent Agent 接口，作为默认 Agent 实现。
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        prompt_builder: PromptBuilder | None = None,
        observation_builder: ObservationBuilder | None = None,
        tool_message_builder: ToolMessageBuilder | None = None,
        planner: Planner | None = None,
        error_handler: AgentErrorHandler | None = None,
        workflow_error_handler: WorkflowErrorHandler | None = None,
        tracer: AgentTracer | None = None,
        trace_collector: TraceCollector | None = None,
        metrics_collector: MetricsCollector | None = None,
        evaluator: Evaluator | None = None,
        client=None,
        tool_manager: ToolManager | None = None,
        retriever=None,
        mcp_server_manager: MCPServerManager | None = None,
    ):

        super().__init__()

        self.config = config or AgentConfig()

        self.metrics_collector = self._setup_metrics(
            metrics_collector,
        )

        self.trace_collector = self._setup_trace_collector(
            trace_collector,
        )

        self.evaluator = self._setup_evaluator(
            evaluator,
        )

        self.tracer = tracer or AgentTracer(
            trace_collector=self.trace_collector,
        )

        self.error_handler = error_handler or AgentErrorHandler()
        self.workflow_error_handler = (
            workflow_error_handler or WorkflowErrorHandler()
        )

        self.last_trace = None
        self.last_evaluation = None
        self.last_metrics = None

        self.mcp_server_manager = self._setup_mcp(
            mcp_server_manager,
        )

        self.tool_manager = tool_manager or ToolManager(
            config=self.config,
            mcp_server_manager=self.mcp_server_manager,
            tracer=self.tracer,
        )

        self.client = client or get_llm_client()
        self.client.bind_tool_manager(
            self.tool_manager
        )

        mcp_resource_provider = None
        mcp_prompt_provider = None

        if self.mcp_server_manager is not None:

            mcp_resource_provider = (
                self.mcp_server_manager.resource_provider
            )

            mcp_prompt_provider = (
                self.mcp_server_manager.prompt_provider
            )

        self.prompt_builder = (
            prompt_builder
            or PromptBuilder(
                config=self.config,
                retriever=retriever,
                mcp_resource_provider=mcp_resource_provider,
                mcp_prompt_provider=mcp_prompt_provider,
                tracer=self.tracer,
            )
        )

        observation_builder = (
            observation_builder or ObservationBuilder()
        )

        self.tool_message_builder = (
            tool_message_builder
            or ToolMessageBuilder(
                observation_builder=observation_builder,
            )
        )

        self.planner = self._create_planner(
            planner,
        )

        self.agent_executor = AgentExecutor(
            client=self.client,
            config=self.config,
            tool_message_builder=self.tool_message_builder,
            tool_manager=self.tool_manager,
            error_handler=self.error_handler,
            tracer=self.tracer,
        )

        self.step_executor = StepExecutor(
            agent_executor=self.agent_executor,
            tool_manager=self.tool_manager,
            prompt_builder=self.prompt_builder,
            config=self.config,
            tracer=self.tracer,
            error_handler=self.workflow_error_handler,
        )

        workflow = SequentialWorkflow(
            config=self.config,
            error_handler=self.workflow_error_handler,
            tracer=self.tracer,
        )

        self.workflow_executor = WorkflowExecutor(
            config=self.config,
            planner=self.planner,
            workflow=workflow,
            step_executor=self.step_executor,
            agent_executor=self.agent_executor,
            tracer=self.tracer,
            error_handler=self.workflow_error_handler,
        )

    def _setup_metrics(
        self,
        metrics_collector: MetricsCollector | None,
    ) -> MetricsCollector | None:

        if (
            not self.config.enable_metrics
            and metrics_collector is None
        ):

            return None

        return metrics_collector or MetricsCollector()

    def _setup_trace_collector(
        self,
        trace_collector: TraceCollector | None,
    ) -> TraceCollector | None:

        needs_collector = (
            self.config.enable_trace
            or self.config.enable_metrics
        )

        if not needs_collector:

            return trace_collector

        if trace_collector is not None:

            return trace_collector

        exporter = None

        if self.config.enable_trace:

            exporter = create_trace_exporter(
                self.config.exporter_type,
            )

        return TraceCollector(
            exporter=exporter,
            metrics_collector=self.metrics_collector,
        )

    def _setup_evaluator(
        self,
        evaluator: Evaluator | None,
    ) -> Evaluator | None:

        if not self.config.enable_evaluation:

            return evaluator

        return evaluator or RuleBasedEvaluator()

    def _create_planner(
        self,
        planner: Planner | None,
    ) -> Planner:

        if planner is not None:

            return planner

        if self.config.enable_planner:

            return LLMPlanner(
                client=self.client,
                config=self.config,
            )

        return NoPlanner()

    def _setup_mcp(
        self,
        mcp_server_manager: MCPServerManager | None,
    ) -> MCPServerManager | None:

        if not self.config.enable_mcp:

            return mcp_server_manager

        manager = (
            mcp_server_manager or MCPServerManager()
        )

        if not manager.get_all_servers():

            server_names = (
                self.config.mcp_servers
                or ["local-mock"]
            )

            for server_name in server_names:

                client = LocalMCPClient(
                    server_name=server_name,
                )

                manager.register_server(client)

                self.tracer.on_mcp_server(
                    server_name,
                    "registered",
                )

        return manager

    def execute(
        self,
        context: AgentContext
    ) -> AgentResult:

        if (
            self.trace_collector is not None
            and self.config.enable_trace
        ):

            self.trace_collector.start_trace(
                session_id=context.session_id,
                metadata={
                    "user_message": context.user_message,
                    "enable_planner": self.config.enable_planner,
                    "enable_rag": self.config.enable_rag,
                    "enable_mcp": self.config.enable_mcp,
                },
            )

        try:

            try:

                messages = self.prompt_builder.build(
                    context
                )

            except MemoryError as error:

                return self.error_handler.handle_memory_error(
                    error
                )

            except Exception as error:

                return self.error_handler.handle_memory_error(
                    error
                )

            self.tracer.on_prompt(messages)

            result = self.workflow_executor.run(
                context,
                messages,
            )

            return result

        finally:

            self._finalize_observability()

    def _finalize_observability(self) -> None:

        if (
            self.trace_collector is not None
            and self.config.enable_trace
        ):

            self.last_trace = (
                self.trace_collector.finish_trace()
            )

            if (
                self.last_trace is not None
                and self.evaluator is not None
            ):

                self.last_evaluation = (
                    self.evaluator.evaluate(
                        self.last_trace
                    )
                )

        if self.metrics_collector is not None:

            self.last_metrics = (
                self.metrics_collector.summarize()
            )

    def replay_last_trace(
        self,
        verbose: bool = True,
    ) -> list[str]:

        if self.last_trace is None:

            return []

        return TracePlayer(
            self.last_trace
        ).play(verbose=verbose)

    @property
    def name(self) -> str:
        return "chat"

    def can_handle(
        self,
        task_input: str,
        metadata: dict | None = None,
    ) -> bool:
        """
        默认 ChatAgent 可处理任意对话任务。
        Multi-Agent 场景下可由专用 Agent 接管特定任务。
        """

        return True

    def get_capabilities(self) -> list[str]:
        """
        根据 AgentConfig 返回当前启用的能力标签。
        """

        capabilities = [
            "chat",
            "tool_calling",
        ]

        if self.config.enable_rag:

            capabilities.append("rag")

        if self.config.enable_mcp:

            capabilities.append("mcp")

        if self.config.enable_planner:

            capabilities.append("planning")

        if self.config.enable_trace:

            capabilities.append("tracing")

        if self.config.enable_multi_agent:

            capabilities.append("multi_agent")

        return capabilities
