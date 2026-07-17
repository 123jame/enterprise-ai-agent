from __future__ import annotations

from applications.platform.platform_result import PermissionAction
from applications.platform.platform_result import PermissionGrant
from applications.platform.platform_result import Role
from applications.platform.platform_store import PlatformStore
from applications.platform.settings import PlatformSettings


class PermissionManager:
    """
    权限管理：Role / User / Agent / Project / Workspace。
    """

    ROLES_KEY = "roles"
    GRANTS_KEY = "grants"

    _DEFAULT_ROLES: dict[str, list[str]] = {
        "admin": ["*"],
        "developer": [
            "project:write",
            "workspace:read",
            "agent:execute",
        ],
        "viewer": [
            "project:read",
            "workspace:read",
        ],
    }

    def __init__(
        self,
        settings: PlatformSettings | None = None,
        store: PlatformStore | None = None,
    ):

        self._settings = settings or PlatformSettings()
        self._store = store or PlatformStore(settings=self._settings)

    def initialize_defaults(self) -> list[Role]:

        if self._store.load(self.ROLES_KEY):

            return self.list_roles()

        roles: list[Role] = []

        for name, permissions in self._DEFAULT_ROLES.items():

            roles.append(self.create_role(name, permissions))

        return roles

    def create_role(
        self,
        name: str,
        permissions: list[str] | None = None,
    ) -> Role:

        role = Role.create(name, permissions)
        self._store.append(self.ROLES_KEY, self._role_to_dict(role))

        return role

    def grant(
        self,
        *,
        subject_type: str,
        subject_id: str,
        resource_type: str,
        resource_id: str,
        action: PermissionAction,
    ) -> PermissionGrant:

        grant = PermissionGrant.create(
            subject_type=subject_type,
            subject_id=subject_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
        )

        self._store.append(self.GRANTS_KEY, self._grant_to_dict(grant))

        return grant

    def check(
        self,
        *,
        subject_type: str,
        subject_id: str,
        resource_type: str,
        resource_id: str,
        action: PermissionAction,
        role_name: str = "developer",
    ) -> bool:

        if not self._settings.enforce_permissions:

            return True

        role = self._find_role(role_name)

        if role and "*" in role.permissions:

            return True

        if role:

            required = f"{resource_type}:{action.value}"

            if required in role.permissions:

                return True

        for item in self._store.load(self.GRANTS_KEY):

            if (
                item.get("subject_type") == subject_type
                and item.get("subject_id") == subject_id
                and item.get("resource_type") == resource_type
                and item.get("resource_id") in (resource_id, "*")
                and item.get("action") == action.value
                and item.get("granted", True)
            ):

                return True

        return False

    def list_roles(self) -> list[Role]:

        return [
            self._dict_to_role(item)
            for item in self._store.load(self.ROLES_KEY)
        ]

    def summarize_permissions(
        self,
        *,
        subject_id: str,
        role_name: str = "developer",
    ) -> str:

        roles = self.list_roles()
        role = next((r for r in roles if r.name == role_name), None)

        grants = [
            item
            for item in self._store.load(self.GRANTS_KEY)
            if item.get("subject_id") == subject_id
        ]

        role_perms = ", ".join(role.permissions) if role else "none"

        return (
            f"Subject: {subject_id}\n"
            f"Role: {role_name} ({role_perms})\n"
            f"Direct grants: {len(grants)}"
        )

    def _find_role(self, name: str) -> Role | None:

        for item in self._store.load(self.ROLES_KEY):

            if item.get("name") == name:

                return self._dict_to_role(item)

        return None

    @staticmethod
    def _role_to_dict(role: Role) -> dict:

        return {
            "id": role.id,
            "name": role.name,
            "permissions": role.permissions,
            "metadata": role.metadata,
        }

    @staticmethod
    def _dict_to_role(data: dict) -> Role:

        return Role(
            id=data["id"],
            name=data["name"],
            permissions=data.get("permissions", []),
            metadata=data.get("metadata", {}),
        )

    @staticmethod
    def _grant_to_dict(grant: PermissionGrant) -> dict:

        return {
            "id": grant.id,
            "subject_type": grant.subject_type,
            "subject_id": grant.subject_id,
            "resource_type": grant.resource_type,
            "resource_id": grant.resource_id,
            "action": grant.action.value,
            "granted": grant.granted,
        }
