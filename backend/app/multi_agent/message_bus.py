from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any
from typing import Callable
from uuid import uuid4


class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"


@dataclass
class AgentMessage:
    """
    Agent 间通信消息。
    """

    sender: str

    receiver: str

    payload: dict[str, Any]

    message_type: MessageType = MessageType.REQUEST

    message_id: str = field(
        default_factory=lambda: uuid4().hex[:12]
    )

    correlation_id: str = ""


def create_request(
    sender: str,
    receiver: str,
    payload: dict[str, Any],
    correlation_id: str = "",
) -> AgentMessage:

    return AgentMessage(
        sender=sender,
        receiver=receiver,
        payload=payload,
        message_type=MessageType.REQUEST,
        correlation_id=correlation_id,
    )


def create_response(
    sender: str,
    receiver: str,
    payload: dict[str, Any],
    correlation_id: str = "",
    success: bool = True,
) -> AgentMessage:

    payload = {
        **payload,
        "success": success,
    }

    return AgentMessage(
        sender=sender,
        receiver=receiver,
        payload=payload,
        message_type=MessageType.RESPONSE,
        correlation_id=correlation_id,
    )


def create_broadcast(
    sender: str,
    payload: dict[str, Any],
) -> AgentMessage:

    return AgentMessage(
        sender=sender,
        receiver="*",
        payload=payload,
        message_type=MessageType.BROADCAST,
    )


# 向后兼容别名
Request = create_request
Response = create_response
Broadcast = create_broadcast

MessageHandler = Callable[[AgentMessage], None]


class MessageBus:
    """
    Agent 消息总线。

    Agent 之间通过 MessageBus 通信，不直接互相依赖。
    """

    def __init__(self):

        self._handlers: dict[str, list[MessageHandler]] = {}
        self._history: list[AgentMessage] = []

    @property
    def history(self) -> list[AgentMessage]:

        return list(self._history)

    def subscribe(
        self,
        agent_name: str,
        handler: MessageHandler,
    ) -> None:

        if agent_name not in self._handlers:

            self._handlers[agent_name] = []

        self._handlers[agent_name].append(handler)

    def publish(
        self,
        message: AgentMessage,
    ) -> None:

        self._history.append(message)

        if message.message_type == MessageType.BROADCAST:

            for handlers in self._handlers.values():

                for handler in handlers:

                    handler(message)

            return

        handlers = self._handlers.get(
            message.receiver,
            [],
        )

        for handler in handlers:

            handler(message)

    def send_request(
        self,
        sender: str,
        receiver: str,
        payload: dict[str, Any],
        correlation_id: str = "",
    ) -> AgentMessage:

        message = create_request(
            sender,
            receiver,
            payload,
            correlation_id,
        )

        self.publish(message)

        return message

    def send_response(
        self,
        sender: str,
        receiver: str,
        payload: dict[str, Any],
        correlation_id: str = "",
        success: bool = True,
    ) -> AgentMessage:

        message = create_response(
            sender,
            receiver,
            payload,
            correlation_id,
            success,
        )

        self.publish(message)

        return message

    def broadcast(
        self,
        sender: str,
        payload: dict[str, Any],
    ) -> AgentMessage:

        message = create_broadcast(
            sender,
            payload,
        )

        self.publish(message)

        return message

    def clear_history(self) -> None:

        self._history.clear()
