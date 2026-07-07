from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass
class SharedMemoryEntry:
    """
    共享内存条目（可序列化快照）。
    """

    key: str

    value: Any

    agent_name: str = ""

    task_id: str = ""


class SharedMemory:
    """
    Multi-Agent 共享内存。

    存储 Context、Intermediate Result、Workflow State 的快照，
    不直接共享 Agent 内部对象。
    """

    def __init__(self):

        self._store: dict[str, SharedMemoryEntry] = {}
        self._workflow_state: dict[str, Any] = {}

    def set(
        self,
        key: str,
        value: Any,
        *,
        agent_name: str = "",
        task_id: str = "",
    ) -> None:

        self._store[key] = SharedMemoryEntry(
            key=key,
            value=value,
            agent_name=agent_name,
            task_id=task_id,
        )

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        entry = self._store.get(key)

        if entry is None:

            return default

        return entry.value

    def get_entry(
        self,
        key: str,
    ) -> SharedMemoryEntry | None:

        return self._store.get(key)

    def delete(
        self,
        key: str,
    ) -> bool:

        if key not in self._store:

            return False

        del self._store[key]

        return True

    def get_context_snapshot(self) -> dict[str, Any]:

        return {
            key: entry.value
            for key, entry in self._store.items()
        }

    def set_workflow_state(
        self,
        state: dict[str, Any],
    ) -> None:

        self._workflow_state = dict(state)

    def get_workflow_state(self) -> dict[str, Any]:

        return dict(self._workflow_state)

    def update_workflow_state(
        self,
        **kwargs: Any,
    ) -> None:

        self._workflow_state.update(kwargs)

    def clear(self) -> None:

        self._store.clear()
        self._workflow_state.clear()
