from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from applications.platform.settings import PlatformSettings


class PlatformStore:
    """
    平台数据持久化（JSON 文件），各 Manager 共享。
    """

    def __init__(
        self,
        settings: PlatformSettings | None = None,
    ):

        self._settings = settings or PlatformSettings()
        self._root = self._settings.platform_data_root
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:

        return self._root

    def load(self, name: str) -> list[dict[str, Any]]:

        path = self._root / f"{name}.json"

        if not path.is_file():

            return []

        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, name: str, data: list[dict[str, Any]]) -> None:

        path = self._root / f"{name}.json"
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def append(self, name: str, item: dict[str, Any]) -> None:

        items = self.load(name)
        items.append(item)
        self.save(name, items)

    def replace(
        self,
        name: str,
        item_id: str,
        item: dict[str, Any],
        *,
        id_field: str = "id",
    ) -> bool:

        items = self.load(name)
        updated = False

        for index, existing in enumerate(items):

            if existing.get(id_field) == item_id:

                items[index] = item
                updated = True
                break

        if updated:

            self.save(name, items)

        return updated

    def find(
        self,
        name: str,
        item_id: str,
        *,
        id_field: str = "id",
    ) -> dict[str, Any] | None:

        for item in self.load(name):

            if item.get(id_field) == item_id:

                return item

        return None

    def filter(
        self,
        name: str,
        **criteria: Any,
    ) -> list[dict[str, Any]]:

        results: list[dict[str, Any]] = []

        for item in self.load(name):

            if all(item.get(k) == v for k, v in criteria.items()):

                results.append(item)

        return results
