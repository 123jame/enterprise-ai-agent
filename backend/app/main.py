from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health_router
from app.api import chat_router
from app.api.dashboard import dashboard_router

app = FastAPI(

    title="Enterprise AI Agent",

    version="0.1.0"
)


@app.get("/")
def root():

    return {
        "name": "Enterprise AI Agent",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "dashboard_api": "/api/v1/dashboard/projects",
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(

    health_router

)

app.include_router(

    chat_router,

    prefix="/api/v1",

    tags=["Chat"]

)

app.include_router(

    dashboard_router,

    prefix="/api/v1",

)