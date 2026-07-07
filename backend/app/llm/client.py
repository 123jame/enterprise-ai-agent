import json
from collections.abc import Generator

from openai import OpenAI

from app.core.config import settings
from app.core.logger import logger
from app.tools.registry import ToolRegistry

from .types import ChatResult
from .types import Message
from .types import ToolCall


class LLMClient:

    def __init__(self):

        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )

        self._tool_manager = None

    def bind_tool_manager(
        self,
        tool_manager,
    ) -> None:
        """
        绑定 ToolManager，统一获取本地 + MCP Tool Schema。
        """

        self._tool_manager = tool_manager

    def _get_tool_schemas(self) -> list[dict]:

        if self._tool_manager is not None:

            return self._tool_manager.get_schemas()

        return ToolRegistry.get_schemas()

    def chat(
        self,
        messages: list[Message],
        use_tools: bool = True,
    ) -> ChatResult:

        logger.info("Calling LLM...")

        request_kwargs = {
            "model": settings.MODEL_NAME,
            "messages": [
                self._serialize_message(message)
                for message in messages
            ],
            "temperature": settings.TEMPERATURE,
            "max_tokens": settings.MAX_TOKENS,
        }

        if use_tools:

            request_kwargs["tools"] = self._get_tool_schemas()
            request_kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(
            **request_kwargs
        )

        logger.info("LLM Finished.")

        message = response.choices[0].message

        if message.tool_calls:

            tool_calls = [
                ToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=self._parse_arguments(
                        tool_call.function.arguments
                    ),
                )
                for tool_call in message.tool_calls
            ]

            return ChatResult(
                model=response.model,
                content=message.content,
                tool_calls=tool_calls,
            )

        return ChatResult(
            model=response.model,
            content=message.content,
        )

    def stream_chat(
        self,
        messages: list[Message]
    ) -> Generator[str, None, None]:

        response = self.client.chat.completions.create(

            model=settings.MODEL_NAME,

            messages=[
                self._serialize_message(message)
                for message in messages
            ],

            stream=True,

            temperature=settings.TEMPERATURE,

            max_tokens=settings.MAX_TOKENS

        )

        for chunk in response:

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta.content

            if delta:

                yield delta

    def _serialize_message(
        self,
        message: Message
    ) -> dict:

        payload: dict = {
            "role": message.role,
        }

        if message.content is not None:

            payload["content"] = message.content

        if message.tool_call_id:

            payload["tool_call_id"] = message.tool_call_id

        if message.name:

            payload["name"] = message.name

        if message.tool_calls:

            payload["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.name,
                        "arguments": json.dumps(
                            tool_call.arguments,
                            ensure_ascii=False,
                        ),
                    },
                }
                for tool_call in message.tool_calls
            ]

        return payload

    @staticmethod
    def _parse_arguments(
        raw_arguments: str | None
    ) -> dict:

        if not raw_arguments:

            return {}

        return json.loads(raw_arguments)
