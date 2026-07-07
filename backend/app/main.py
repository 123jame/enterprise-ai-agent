from fastapi import FastAPI

from app.api import health_router
from app.api import chat_router

app = FastAPI(

    title="Enterprise AI Agent",

    version="0.1.0"
)

app.include_router(

    health_router

)

app.include_router(

    chat_router,

    prefix="/api/v1",

    tags=["Chat"]

)