from fastapi import APIRouter

from app.schemas.chat import ChatRequest
from app.schemas.chat import ChatResponse

from app.services.chat_service import ChatService

router = APIRouter()

service = ChatService()


@router.post(
    "/chat",
    response_model=ChatResponse
)
def chat(
    request: ChatRequest
):

    return service.chat(

        session_id=request.session_id,

        user_message=request.message

    )