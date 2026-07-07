from app.agents.factory import AgentFactory
from app.agents.types import AgentContext

from app.schemas.chat import ChatResponse


class ChatService:

    def chat(
        self,
        session_id: str,
        user_message: str
    ) -> ChatResponse:

        context = AgentContext(

            session_id=session_id,

            user_message=user_message

        )

        agent = AgentFactory.get(
            "chat"
        )

        result = agent.run(
            context
        )

        return ChatResponse(

            success=result.success,

            model=result.model,

            answer=result.content

        )