from __future__ import annotations

from app.memory.manager import MemoryManager
from app.memory.types import MemoryRecord

from applications.platform.platform_result import MemoryScopeContext
from applications.platform.platform_result import PlatformEventType


class PlatformMemoryHelper:
    """
    平台 Memory 作用域辅助，不修改 Framework Memory 实现。
    """

    @staticmethod
    def save(
        memory_manager: MemoryManager | None,
        session_id: str,
        content: str,
        *,
        event_type: PlatformEventType,
        scope: MemoryScopeContext | None = None,
        metadata: dict | None = None,
    ) -> None:

        if memory_manager is None or not session_id:

            return

        record_metadata = {
            "type": "memory",
            "category": event_type.value,
            **(scope.to_metadata() if scope else {}),
            **(metadata or {}),
        }

        memory_manager.memory.save(
            session_id,
            MemoryRecord(
                role="assistant",
                content=content,
                metadata=record_metadata,
            ),
        )

    @staticmethod
    def scoped_session_id(
        base_session_id: str,
        scope: MemoryScopeContext,
    ) -> str:

        parts = [base_session_id]

        if scope.organization_id:

            parts.append(f"org:{scope.organization_id}")

        if scope.workspace_id:

            parts.append(f"ws:{scope.workspace_id}")

        if scope.project_id:

            parts.append(f"proj:{scope.project_id}")

        if scope.user_id:

            parts.append(f"user:{scope.user_id}")

        return ":".join(parts)
