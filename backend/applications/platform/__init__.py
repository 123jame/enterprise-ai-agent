from applications.platform.platform_result import PlatformContext

__all__ = [
    "AuditManager",
    "ConfigurationManager",
    "EnterpriseCoordinator",
    "EnterpriseCoordinatorResult",
    "EnterpriseWorkspaceManager",
    "GovernanceManager",
    "ModelManager",
    "OrganizationManager",
    "PermissionManager",
    "PlatformContext",
    "PlatformMemoryHelper",
    "PlatformSettings",
    "ProjectRegistry",
    "TeamManager",
]


def __getattr__(name: str):

    if name == "AuditManager":
        from applications.platform.audit_manager import AuditManager

        return AuditManager

    if name == "ConfigurationManager":
        from applications.platform.configuration_manager import ConfigurationManager

        return ConfigurationManager

    if name == "EnterpriseCoordinator":
        from applications.platform.enterprise_coordinator import EnterpriseCoordinator

        return EnterpriseCoordinator

    if name == "EnterpriseCoordinatorResult":
        from applications.platform.enterprise_coordinator import (
            EnterpriseCoordinatorResult,
        )

        return EnterpriseCoordinatorResult

    if name == "EnterpriseWorkspaceManager":
        from applications.platform.workspace_manager import EnterpriseWorkspaceManager

        return EnterpriseWorkspaceManager

    if name == "GovernanceManager":
        from applications.platform.governance_manager import GovernanceManager

        return GovernanceManager

    if name == "ModelManager":
        from applications.platform.model_manager import ModelManager

        return ModelManager

    if name == "OrganizationManager":
        from applications.platform.organization_manager import OrganizationManager

        return OrganizationManager

    if name == "PermissionManager":
        from applications.platform.permission_manager import PermissionManager

        return PermissionManager

    if name == "PlatformMemoryHelper":
        from applications.platform.platform_memory import PlatformMemoryHelper

        return PlatformMemoryHelper

    if name == "PlatformSettings":
        from applications.platform.settings import PlatformSettings

        return PlatformSettings

    if name == "ProjectRegistry":
        from applications.platform.project_registry import ProjectRegistry

        return ProjectRegistry

    if name == "TeamManager":
        from applications.platform.team_manager import TeamManager

        return TeamManager

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
