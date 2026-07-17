from applications.dashboard.dashboard_service import DashboardService
from applications.dashboard.run_service import DashboardRunService

__all__ = [
    "DashboardEventListener",
    "DashboardRunService",
    "DashboardService",
    "EventBus",
    "get_dashboard_service",
    "get_event_bus",
    "get_run_service",
]


def __getattr__(name: str):

    if name == "DashboardEventListener":
        from applications.dashboard.event_listener import DashboardEventListener

        return DashboardEventListener

    if name == "DashboardRunService":
        from applications.dashboard.run_service import DashboardRunService

        return DashboardRunService

    if name == "DashboardService":
        from applications.dashboard.dashboard_service import DashboardService

        return DashboardService

    if name == "EventBus":
        from applications.dashboard.event_bus import EventBus

        return EventBus

    if name == "get_dashboard_service":
        from applications.dashboard.dashboard_service import get_dashboard_service

        return get_dashboard_service

    if name == "get_event_bus":
        from applications.dashboard.event_bus import get_event_bus

        return get_event_bus

    if name == "get_run_service":
        from applications.dashboard.run_service import get_run_service

        return get_run_service

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
