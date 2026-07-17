from __future__ import annotations

import json
from pathlib import Path

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.knowledge.knowledge_result import KnowledgeCategory
from applications.software_team.knowledge.knowledge_result import KnowledgeEntry


class KnowledgeRepository:
    """
    知识存储：Architecture / PRD / Code Pattern / Best Practice /
    Issue / Solution / Design Decision。
    """

    KNOWLEDGE_DIR = "knowledge"
    CATALOG_FILE = "catalog.json"
    ENTRIES_DIR = "entries"

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()

    def save(
        self,
        workspace: str | Path,
        entry: KnowledgeEntry,
    ) -> str:

        root = self._ensure_dirs(workspace)
        entry_path = root / self.ENTRIES_DIR / f"{entry.id}.json"

        entry_path.write_text(
            json.dumps(self._entry_to_dict(entry), ensure_ascii=False, indent=2),
            encoding=DEFAULT_ENCODING,
        )

        catalog = self._load_catalog(root)
        catalog[entry.id] = {
            "id": entry.id,
            "title": entry.title,
            "category": entry.category.value,
            "source_path": entry.source_path,
            "project_id": entry.project_id,
            "agent_name": entry.agent_name,
            "created_at": entry.created_at,
        }

        self._save_catalog(root, catalog)

        return str(entry_path)

    def load(
        self,
        workspace: str | Path,
        entry_id: str,
    ) -> KnowledgeEntry | None:

        root = self._knowledge_root(workspace)
        entry_path = root / self.ENTRIES_DIR / f"{entry_id}.json"

        if not entry_path.is_file():

            return None

        data = json.loads(
            entry_path.read_text(encoding=DEFAULT_ENCODING),
        )

        return self._dict_to_entry(data)

    def list_entries(
        self,
        workspace: str | Path,
        *,
        category: KnowledgeCategory | None = None,
        project_id: str = "",
    ) -> list[KnowledgeEntry]:

        root = self._knowledge_root(workspace)

        if not root.is_dir():

            return []

        entries: list[KnowledgeEntry] = []
        entries_dir = root / self.ENTRIES_DIR

        if not entries_dir.is_dir():

            return []

        for path in entries_dir.glob("*.json"):

            try:

                data = json.loads(path.read_text(encoding=DEFAULT_ENCODING))
                entry = self._dict_to_entry(data)

            except (json.JSONDecodeError, KeyError, ValueError):

                continue

            if category is not None and entry.category != category:

                continue

            if project_id and entry.project_id != project_id:

                continue

            entries.append(entry)

        return entries

    def delete(
        self,
        workspace: str | Path,
        entry_id: str,
    ) -> bool:

        root = self._knowledge_root(workspace)
        entry_path = root / self.ENTRIES_DIR / f"{entry_id}.json"

        if not entry_path.is_file():

            return False

        entry_path.unlink()

        catalog = self._load_catalog(root)
        catalog.pop(entry_id, None)
        self._save_catalog(root, catalog)

        return True

    def _ensure_dirs(self, workspace: str | Path) -> Path:

        root = self._knowledge_root(workspace)
        (root / self.ENTRIES_DIR).mkdir(parents=True, exist_ok=True)

        catalog_path = root / self.CATALOG_FILE

        if not catalog_path.is_file():

            catalog_path.write_text("{}", encoding=DEFAULT_ENCODING)

        return root

    @staticmethod
    def _knowledge_root(workspace: str | Path) -> Path:

        return Path(workspace).resolve() / KnowledgeRepository.KNOWLEDGE_DIR

    @staticmethod
    def _load_catalog(root: Path) -> dict:

        catalog_path = root / KnowledgeRepository.CATALOG_FILE

        if not catalog_path.is_file():

            return {}

        return json.loads(catalog_path.read_text(encoding=DEFAULT_ENCODING))

    @staticmethod
    def _save_catalog(root: Path, catalog: dict) -> None:

        catalog_path = root / KnowledgeRepository.CATALOG_FILE

        catalog_path.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2),
            encoding=DEFAULT_ENCODING,
        )

    @staticmethod
    def _entry_to_dict(entry: KnowledgeEntry) -> dict:

        return {
            "id": entry.id,
            "title": entry.title,
            "category": entry.category.value,
            "content": entry.content,
            "source_path": entry.source_path,
            "document_type": entry.document_type.value,
            "tags": entry.tags,
            "project_id": entry.project_id,
            "agent_name": entry.agent_name,
            "created_at": entry.created_at,
            "metadata": entry.metadata,
        }

    @staticmethod
    def _dict_to_entry(data: dict) -> KnowledgeEntry:

        from applications.software_team.knowledge.knowledge_result import (
            DocumentType,
        )

        return KnowledgeEntry(
            id=data["id"],
            title=data["title"],
            category=KnowledgeCategory(data["category"]),
            content=data["content"],
            source_path=data.get("source_path", ""),
            document_type=DocumentType(
                data.get("document_type", DocumentType.MARKDOWN.value),
            ),
            tags=data.get("tags", []),
            project_id=data.get("project_id", ""),
            agent_name=data.get("agent_name", ""),
            created_at=data.get("created_at", ""),
            metadata=data.get("metadata", {}),
        )
