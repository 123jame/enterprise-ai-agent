from pydantic import BaseModel


class ChatRequest(BaseModel):

    session_id: str

    message: str


class ChatResponse(BaseModel):

    success: bool

    model: str

    answer: str