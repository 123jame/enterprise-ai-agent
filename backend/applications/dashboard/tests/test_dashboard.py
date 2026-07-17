"""
P13 Visualization Dashboard 测试。

运行:
    cd backend
    python -m applications.dashboard.tests.test_dashboard
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from applications.dashboard.dashboard_service import DashboardService
from applications.dashboard.event_bus import get_event_bus
from applications.dashboard.event_types import DashboardEventType
from applications.dashboard.state_store import get_state_store
from applications.platform.settings import PlatformSettings


def test_dashboard_service() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        settings = PlatformSettings(
            enable_platform=True,
            platform_data_root=Path(tmp) / "platform_data",
            workspace_root=Path(tmp) / "workspace",
        )
        service = DashboardService(platform_settings=settings)

        org = service.get_organization()
        assert org.get("organization_id")
        assert "workspaces" in org

        config = service.get_settings()
        assert "llm" in config
        assert "model" in config

        print("DashboardService: PASS")


def test_event_bus() -> None:

    bus = get_event_bus()
    event = bus.emit(
        DashboardEventType.LOG,
        project_id="p1",
        session_id="s1",
        payload={"message": "test"},
    )

    assert event.type == DashboardEventType.LOG
    assert bus.history[-1].project_id == "p1"

    print("EventBus: PASS")


def test_state_store() -> None:

    store = get_state_store()
    state = store.create_project(
        project_id="proj-1",
        session_id="sess-1",
        name="Demo",
        requirement="Build demo",
    )

    store.mark_agent_started("proj-1", "ProductAgent", task="Write PRD")
    store.mark_agent_finished("proj-1", "ProductAgent", success=True)

    loaded = store.get("proj-1")
    assert loaded is not None
    assert loaded.agents["ProductAgent"].status == "completed"

    print("DashboardStateStore: PASS")


def test_failed_project_does_not_mark_completed_stage_failed() -> None:

    store = get_state_store()
    state = store.create_project(
        project_id="proj-failed",
        session_id="sess-failed",
        name="Failed Demo",
        requirement="Build demo",
    )

    store.set_stage("proj-failed", "development", status="active")
    store.finish_project("proj-failed", success=False)

    loaded = store.get("proj-failed")
    assert loaded is not None
    assert loaded.status == "failed"

    completed_stage = next(
        stage for stage in loaded.workflow_stages if stage.id == "completed"
    )
    development_stage = next(
        stage for stage in loaded.workflow_stages if stage.id == "development"
    )

    assert completed_stage.status == "pending"
    assert development_stage.status == "failed"

    print("Failed project stage mapping: PASS")


def test_dashboard_api() -> None:

    client = TestClient(app)

    response = client.get("/api/v1/dashboard/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    response = client.get("/api/v1/dashboard/organization")
    assert response.status_code == 200
    assert "workspaces" in response.json()

    response = client.get("/api/v1/dashboard/settings")
    assert response.status_code == 200

    response = client.post(
        "/api/v1/dashboard/projects",
        json={
            "requirement": "开发测试系统",
            "project_name": "Test Dashboard",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert body["project_id"]

    print("Dashboard API: PASS")


def main() -> None:

    test_dashboard_service()
    test_event_bus()
    test_state_store()
    test_failed_project_does_not_mark_completed_stage_failed()
    test_dashboard_api()

    print("\n=== P13 Visualization Dashboard: ALL PASS ===")


if __name__ == "__main__":

    main()
