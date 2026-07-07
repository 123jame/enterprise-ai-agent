from pathlib import Path
from typing import TYPE_CHECKING

from app.llm.types import Message
from app.memory.manager import MemoryManager
from app.memory.types import MemoryRecord
from app.runtime.config import AgentConfig

if TYPE_CHECKING:
    from app.agents.types import AgentContext
    from app.mcp.prompt_provider import MCPPromptProvider
    from app.mcp.resource import MCPResourceProvider
    from app.rag.retriever import Retriever
    from app.rag.types import ScoredDocument
    from app.runtime.tracer import AgentTracer


class PromptBuilder:
    """
    将 AgentContext 组装为 LLM 消息列表。

    单一职责：Prompt 拼接，不关心 Agent Loop、Tool 或 LLM 调用。
    Memory / RAG / MCP Resource 注入也在此完成，与 Agent 解耦。
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        system_prompt: str | None = None,
        system_prompt_path: Path | None = None,
        memory_manager: MemoryManager | None = None,
        retriever: "Retriever | None" = None,
        mcp_resource_provider: "MCPResourceProvider | None" = None,
        mcp_prompt_provider: "MCPPromptProvider | None" = None,
        tracer: "AgentTracer | None" = None,
    ):

        self._config = config or AgentConfig()

        if system_prompt is not None:

            self._system_prompt = system_prompt

        elif self._config.system_prompt is not None:

            self._system_prompt = self._config.system_prompt

        elif system_prompt_path is not None:

            self._system_prompt = system_prompt_path.read_text(
                encoding="utf-8"
            )

        elif self._config.system_prompt_path is not None:

            self._system_prompt = (
                self._config.system_prompt_path.read_text(
                    encoding="utf-8"
                )
            )

        else:

            self._system_prompt = ""

        self._memory_manager = (
            memory_manager or MemoryManager()
        )

        self._retriever = retriever
        self._mcp_resource_provider = mcp_resource_provider
        self._mcp_prompt_provider = mcp_prompt_provider
        self._tracer = tracer

    def build(
        self,
        context: "AgentContext",
        completed_steps: list | None = None,
    ) -> list[Message]:

        memory_context = self._memory_manager.load(
            context.session_id
        )

        records = memory_context.records

        context.history = records

        if self._tracer is not None:

            memory_count = sum(
                1
                for record in records
                if record.metadata.get("type") == "memory"
            )

            self._tracer.on_memory_load(
                session_id=context.session_id,
                record_count=len(records),
                memory_record_count=memory_count,
            )

        messages: list[Message] = []

        messages.append(
            self._build_system_message()
        )

        messages.extend(
            self._build_history_messages(records)
        )

        messages.extend(
            self._build_memory_messages(records)
        )

        messages.extend(
            self._build_rag_messages(
                context.user_message
            )
        )

        messages.extend(
            self._build_mcp_resource_messages()
        )

        messages.extend(
            self._build_mcp_prompt_messages(
                context
            )
        )

        messages.extend(
            self._build_plan_messages(
                context,
                completed_steps or [],
            )
        )

        messages.append(
            self._build_user_message(context)
        )

        return messages

    def _build_system_message(self) -> Message:

        return Message(
            role="system",
            content=self._system_prompt
        )

    def _build_history_messages(
        self,
        records: list[MemoryRecord]
    ) -> list[Message]:

        return [
            Message(
                role=record.role,
                content=record.content
            )
            for record in records
            if record.role in ("user", "assistant")
            and record.metadata.get("type") != "memory"
        ]

    def _build_memory_messages(
        self,
        records: list[MemoryRecord]
    ) -> list[Message]:

        memory_records = [
            record
            for record in records
            if record.metadata.get("type") == "memory"
        ]

        if not memory_records:

            return []

        memory_text = "\n".join(
            record.content
            for record in memory_records
        )

        return [
            Message(
                role="system",
                content=(
                    "The following is relevant memory "
                    f"from previous sessions:\n{memory_text}"
                ),
            )
        ]

    def _build_rag_messages(
        self,
        query: str,
    ) -> list[Message]:

        if not self._config.enable_rag:

            return []

        if self._retriever is None:

            return []

        results = self._retriever.retrieve(
            query=query,
            top_k=self._config.top_k,
            score_threshold=self._config.score_threshold,
        )

        if not results:

            if self._tracer is not None:

                self._tracer.on_rag_retrieval(
                    query,
                    results,
                    embedding_provider=self._embedding_provider_name(),
                    top_k=self._config.top_k,
                    injected_content="",
                )

            return []

        rag_message = self._format_rag_message(results)

        if self._tracer is not None:

            self._tracer.on_rag_retrieval(
                query,
                results,
                embedding_provider=self._embedding_provider_name(),
                top_k=self._config.top_k,
                injected_content=rag_message.content or "",
            )

        return [rag_message]

    def _build_mcp_resource_messages(
        self,
    ) -> list[Message]:
        """
        可插拔注入 MCP Resource。

        最佳实践：放在 History / RAG 之后、User 消息之前。
        """

        if not self._config.enable_mcp:

            return []

        if not self._config.auto_discover_resources:

            return []

        if self._mcp_resource_provider is None:

            return []

        resources = self._mcp_resource_provider.list_resources()

        if not resources:

            return []

        sections: list[str] = []

        for resource in resources:

            content = self._mcp_resource_provider.read_resource(
                resource.id
            )

            if self._tracer is not None:

                self._tracer.on_mcp_resource(
                    server_name=resource.server_name,
                    resource_id=resource.id,
                    content_preview=content.content,
                )

            sections.append(
                f"[{resource.name}] "
                f"({resource.description})\n"
                f"{content.content}"
            )

        return [
            Message(
                role="system",
                content=(
                    "The following MCP resources may help "
                    "answer the user's question:\n\n"
                    + "\n\n".join(sections)
                ),
            )
        ]

    def _build_mcp_prompt_messages(
        self,
        context: "AgentContext",
    ) -> list[Message]:
        """
        可选引用 MCP Prompt 模板。
        """

        if not self._config.enable_mcp:

            return []

        if not self._config.enable_mcp_prompts:

            return []

        if self._mcp_prompt_provider is None:

            return []

        prompt_name = self._config.mcp_prompt_name

        if not prompt_name:

            return []

        prompt_result = self._mcp_prompt_provider.get_prompt(
            name=prompt_name,
            arguments={
                "topic": context.user_message,
            },
        )

        if self._tracer is not None:

            if "." in prompt_name:

                server_name, name = prompt_name.split(
                    ".",
                    maxsplit=1,
                )

            else:

                server_name = "unknown"
                name = prompt_name

            self._tracer.on_mcp_prompt(
                server_name=server_name,
                prompt_name=name,
            )

        return [
            Message(
                role=message.role,
                content=message.content,
            )
            for message in prompt_result.messages
        ]

    def _format_rag_message(
        self,
        results: "list[ScoredDocument]",
    ) -> Message:

        sections: list[str] = []

        for index, scored in enumerate(results, start=1):

            source = scored.document.metadata.get(
                "source",
                scored.document.id,
            )

            sections.append(
                f"[{index}] (score={scored.score:.4f}, "
                f"source={source})\n"
                f"{scored.document.content}"
            )

        knowledge_text = "\n\n".join(sections)

        return Message(
            role="system",
            content=(
                "Use the following retrieved knowledge to "
                "answer the user's question. If the knowledge "
                "is insufficient, say so clearly.\n\n"
                f"{knowledge_text}"
            ),
        )

    def _build_plan_messages(
        self,
        context: "AgentContext",
        completed_steps: list,
    ) -> list[Message]:
        """
        注入当前 Plan、Step 与历史 Step Result，让 LLM 感知执行进度。
        """

        plan = context.plan

        if plan is None:

            return []

        sections: list[str] = [
            f"Goal: {plan.goal}",
            f"Plan status: {plan.status.value}",
        ]

        if context.current_step is not None:

            sections.append(
                "Current step "
                f"[{context.current_step.id}]: "
                f"{context.current_step.description}"
            )

            if context.current_step.tool:

                sections.append(
                    f"Suggested tool: {context.current_step.tool}"
                )

        if completed_steps:

            sections.append("Completed steps:")

            for step in completed_steps:

                sections.append(
                    f"- [{step.id}] {step.description} => "
                    f"{step.result[:200]}"
                )

        return [
            Message(
                role="system",
                content=(
                    "You are executing a multi-step plan. "
                    "Focus on the current step and use completed "
                    "step results when helpful.\n\n"
                    + "\n".join(sections)
                ),
            )
        ]

    def _build_user_message(
        self,
        context: "AgentContext"
    ) -> Message:

        return Message(
            role="user",
            content=context.user_message
        )

    def _embedding_provider_name(self) -> str:
        """
        获取 Embedding Provider 名称，便于 Retrieval Trace。
        """

        if self._retriever is None:

            return ""

        provider = getattr(
            self._retriever,
            "_embedding_provider",
            None,
        )

        if provider is None:

            return type(self._retriever).__name__

        return type(provider).__name__
