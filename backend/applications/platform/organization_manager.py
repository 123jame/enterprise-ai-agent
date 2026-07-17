from __future__ import annotations

from applications.platform.platform_result import Department
from applications.platform.platform_result import Member
from applications.platform.platform_result import Organization
from applications.platform.platform_store import PlatformStore
from applications.platform.settings import PlatformSettings


class OrganizationManager:
    """
    企业组织管理：Department / Team / Member。
    """

    STORE_KEY = "organizations"

    def __init__(
        self,
        settings: PlatformSettings | None = None,
        store: PlatformStore | None = None,
    ):

        self._settings = settings or PlatformSettings()
        self._store = store or PlatformStore(settings=self._settings)

    def create_organization(self, name: str) -> Organization:

        org = Organization.create(name)
        self._store.append(self.STORE_KEY, self._org_to_dict(org))

        return org

    def get_organization(self, org_id: str) -> Organization | None:

        data = self._store.find(self.STORE_KEY, org_id)

        if data is None:

            return None

        return self._dict_to_org(data)

    def get_or_create_default(self) -> Organization:

        items = self._store.load(self.STORE_KEY)

        if items:

            return self._dict_to_org(items[0])

        return self.create_organization(
            self._settings.default_organization_name,
        )

    def add_department(
        self,
        org_id: str,
        department: Department,
    ) -> Organization | None:

        org = self.get_organization(org_id)

        if org is None:

            return None

        org.departments.append(department)
        self._store.replace(
            self.STORE_KEY,
            org_id,
            self._org_to_dict(org),
        )

        return org

    def add_member(
        self,
        org_id: str,
        member: Member,
    ) -> Organization | None:

        org = self.get_organization(org_id)

        if org is None:

            return None

        org.members.append(member)
        self._store.replace(
            self.STORE_KEY,
            org_id,
            self._org_to_dict(org),
        )

        return org

    def list_organizations(self) -> list[Organization]:

        return [
            self._dict_to_org(item)
            for item in self._store.load(self.STORE_KEY)
        ]

    @staticmethod
    def summarize(org: Organization) -> str:

        return (
            f"{org.name} (id={org.id})\n"
            f"Departments: {len(org.departments)}\n"
            f"Members: {len(org.members)}\n"
            f"Teams: {len(org.teams)}"
        )

    @staticmethod
    def _org_to_dict(org: Organization) -> dict:

        return {
            "id": org.id,
            "name": org.name,
            "departments": [
                {
                    "id": d.id,
                    "name": d.name,
                    "description": d.description,
                    "metadata": d.metadata,
                }
                for d in org.departments
            ],
            "members": [
                {
                    "id": m.id,
                    "name": m.name,
                    "email": m.email,
                    "role": m.role,
                    "department_id": m.department_id,
                    "metadata": m.metadata,
                }
                for m in org.members
            ],
            "teams": org.teams,
            "created_at": org.created_at,
            "metadata": org.metadata,
        }

    @staticmethod
    def _dict_to_org(data: dict) -> Organization:

        return Organization(
            id=data["id"],
            name=data["name"],
            departments=[
                Department(
                    id=d["id"],
                    name=d["name"],
                    description=d.get("description", ""),
                    metadata=d.get("metadata", {}),
                )
                for d in data.get("departments", [])
            ],
            members=[
                Member(
                    id=m["id"],
                    name=m["name"],
                    email=m.get("email", ""),
                    role=m.get("role", "member"),
                    department_id=m.get("department_id", ""),
                    metadata=m.get("metadata", {}),
                )
                for m in data.get("members", [])
            ],
            teams=data.get("teams", []),
            created_at=data.get("created_at", ""),
            metadata=data.get("metadata", {}),
        )
