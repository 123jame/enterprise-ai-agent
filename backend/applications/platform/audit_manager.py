from __future__ import annotations

from applications.platform.platform_result import AuditCategory
from applications.platform.platform_result import AuditRecord
from applications.platform.platform_store import PlatformStore
from applications.platform.settings import PlatformSettings


class AuditManager:
    """
    完整审计：Prompt / Tool Call / Memory / Workflow / Deployment / Git / Project / Operation。
    """

    STORE_KEY = "audit"

    def __init__(
        self,
        settings: PlatformSettings | None = None,
        store: PlatformStore | None = None,
    ):

        self._settings = settings or PlatformSettings()
        self._store = store or PlatformStore(settings=self._settings)

    def record(
        self,
        *,
        category: AuditCategory,
        actor: str,
        action: str,
        resource: str,
        detail: str = "",
        metadata: dict | None = None,
    ) -> AuditRecord:

        audit = AuditRecord.create(
            category=category,
            actor=actor,
            action=action,
            resource=resource,
            detail=detail,
            metadata=metadata,
        )

        self._store.append(self.STORE_KEY, self._to_dict(audit))

        return audit

    def record_prompt(
        self,
        *,
        actor: str,
        agent_name: str,
        detail: str = "",
    ) -> AuditRecord:

        return self.record(
            category=AuditCategory.PROMPT,
            actor=actor,
            action="build_prompt",
            resource=agent_name,
            detail=detail[:500],
        )

    def record_workflow(
        self,
        *,
        actor: str,
        project_id: str,
        action: str,
        detail: str = "",
    ) -> AuditRecord:

        return self.record(
            category=AuditCategory.WORKFLOW,
            actor=actor,
            action=action,
            resource=project_id,
            detail=detail,
        )

    def record_platform(
        self,
        *,
        actor: str,
        action: str,
        resource: str,
        detail: str = "",
    ) -> AuditRecord:

        return self.record(
            category=AuditCategory.PLATFORM,
            actor=actor,
            action=action,
            resource=resource,
            detail=detail,
        )

    def list_records(
        self,
        *,
        category: AuditCategory | None = None,
        resource: str = "",
        limit: int = 100,
    ) -> list[AuditRecord]:

        records = [self._from_dict(item) for item in self._store.load(self.STORE_KEY)]

        if category is not None:

            records = [r for r in records if r.category == category]

        if resource:

            records = [r for r in records if r.resource == resource]

        return records[-limit:]

    def summarize(self, limit: int = 10) -> str:

        records = self.list_records(limit=limit)

        if not records:

            return "Audit: no records"

        lines = [f"Audit: {len(records)} recent record(s)"]

        for record in records[-5:]:

            lines.append(
                f"- [{record.category.value}] {record.actor} "
                f"{record.action} on {record.resource}"
            )

        return "\n".join(lines)

    @staticmethod
    def _to_dict(record: AuditRecord) -> dict:

        return {
            "id": record.id,
            "category": record.category.value,
            "actor": record.actor,
            "action": record.action,
            "resource": record.resource,
            "detail": record.detail,
            "timestamp": record.timestamp,
            "metadata": record.metadata,
        }

    @staticmethod
    def _from_dict(data: dict) -> AuditRecord:

        return AuditRecord(
            id=data["id"],
            category=AuditCategory(data["category"]),
            actor=data["actor"],
            action=data["action"],
            resource=data["resource"],
            detail=data.get("detail", ""),
            timestamp=data.get("timestamp", ""),
            metadata=data.get("metadata", {}),
        )
