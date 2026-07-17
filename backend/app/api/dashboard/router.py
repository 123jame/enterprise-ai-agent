from __future__ import annotations

from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from app.api.dashboard.schemas import CreateProjectRequest
from app.api.dashboard.schemas import CreateProjectResponse
from applications.dashboard.dashboard_service import get_dashboard_service
from applications.dashboard.event_bus import get_event_bus
from applications.dashboard.run_service import get_run_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/projects")
def list_projects():

    return get_dashboard_service().list_projects()


@router.post("/projects", response_model=CreateProjectResponse)
def create_project(body: CreateProjectRequest):

    result = get_run_service().start_project(
        requirement=body.requirement,
        project_name=body.project_name,
        user_id=body.user_id,
    )

    return CreateProjectResponse(**result)


@router.get("/projects/{project_id}")
def get_project(project_id: str):

    project = get_dashboard_service().get_project(project_id)

    if project is None:

        return {"error": "Project not found"}

    return project


@router.get("/projects/{project_id}/detail")
def get_project_detail(project_id: str):

    return get_dashboard_service().get_project_detail(project_id)


@router.get("/workflow/{project_id}")
def get_workflow(project_id: str):

    return get_dashboard_service().get_workflow(project_id)


@router.get("/agents")
def list_agents(project_id: str = ""):

    return get_dashboard_service().get_agents(project_id)


@router.get("/git/{project_id}")
def get_git(project_id: str):

    return get_dashboard_service().get_git(project_id)


@router.get("/deployment/{project_id}")
def get_deployment(project_id: str):

    return get_dashboard_service().get_deployment(project_id)


@router.get("/operations/{project_id}")
def get_operations(project_id: str):

    return get_dashboard_service().get_operations(project_id)


@router.get("/knowledge")
def get_knowledge(project_id: str = ""):

    return get_dashboard_service().get_knowledge(project_id)


@router.get("/organization")
def get_organization():

    return get_dashboard_service().get_organization()


@router.get("/settings")
def get_settings():

    return get_dashboard_service().get_settings()


@router.get("/memory/{session_id}")
def get_memory(session_id: str):

    return get_dashboard_service().get_memory(session_id)


@router.get("/prompts/debug/{project_id}")
def get_prompt_debug(project_id: str):

    return get_dashboard_service().get_prompt_debug(project_id)


@router.websocket("/ws")
async def dashboard_websocket(websocket: WebSocket):

    bus = get_event_bus()

    await bus.connect(websocket)

    try:

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        bus.disconnect(websocket)
