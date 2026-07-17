from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.knowledge.knowledge_repository import KnowledgeRepository
from applications.software_team.knowledge.knowledge_result import DocumentType
from applications.software_team.knowledge.knowledge_result import IndexRecord
from applications.software_team.knowledge.knowledge_result import KnowledgeCategory
from applications.software_team.knowledge.knowledge_result import KnowledgeEntry


class DocumentIndexer:
    """
    建立统一文档索引，支持 Markdown / Code / Architecture / API。
    """

    INDEX_FILE = "index.json"

    _CODE_EXTENSIONS = frozenset({
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs",
    })

    _MARKDOWN_EXTENSIONS = frozenset({".md", ".markdown"})

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        repository: KnowledgeRepository | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._repo = repository or KnowledgeRepository(settings=self._settings)

    def index_workspace(
        self,
        workspace: str | Path,
        *,
        project_id: str = "",
    ) -> list[IndexRecord]:

        workspace_path = Path(workspace).resolve()
        records: list[IndexRecord] = []

        scan_paths = [
            (workspace_path / "docs", DocumentType.MARKDOWN),
            (workspace_path / "backend", DocumentType.CODE),
            (workspace_path / "frontend", DocumentType.CODE),
            (workspace_path, DocumentType.MARKDOWN),
        ]

        for base_path, default_type in scan_paths:

            if not base_path.is_dir() and not base_path.is_file():

                continue

            targets = [base_path] if base_path.is_file() else base_path.rglob("*")

            for file_path in targets:

                if not file_path.is_file():

                    continue

                record = self._index_file(
                    workspace_path,
                    file_path,
                    default_type,
                )

                if record is not None:

                    records.append(record)

        entries = self._repo.list_entries(workspace_path, project_id=project_id)

        for entry in entries:

            records.append(self._index_entry(entry))

        self._save_index(workspace_path, records)

        return records

    def index_entry(
        self,
        workspace: str | Path,
        entry: KnowledgeEntry,
    ) -> IndexRecord:

        workspace_path = Path(workspace).resolve()
        record = self._index_entry(entry)
        existing = self.load_index(workspace_path)
        merged = {r.entry_id: r for r in existing}
        merged[record.entry_id] = record
        self._save_index(workspace_path, list(merged.values()))

        return record

    def load_index(
        self,
        workspace: str | Path,
    ) -> list[IndexRecord]:

        index_path = self._index_path(workspace)

        if not index_path.is_file():

            return []

        data = json.loads(index_path.read_text(encoding=DEFAULT_ENCODING))

        return [
            IndexRecord(
                entry_id=item["entry_id"],
                title=item["title"],
                category=item["category"],
                document_type=item["document_type"],
                source_path=item["source_path"],
                token_count=item.get("token_count", 0),
                keywords=item.get("keywords", []),
                vector=item.get("vector", {}),
            )
            for item in data
        ]

    def _index_file(
        self,
        workspace: Path,
        file_path: Path,
        default_type: DocumentType,
    ) -> IndexRecord | None:

        suffix = file_path.suffix.lower()

        if suffix in self._MARKDOWN_EXTENSIONS:

            doc_type = DocumentType.MARKDOWN

        elif suffix in self._CODE_EXTENSIONS:

            doc_type = DocumentType.CODE

        elif suffix == ".pdf":

            doc_type = DocumentType.PDF

        else:

            return None

        if file_path.name in ("catalog.json", "index.json"):

            return None

        try:

            content = file_path.read_text(
                encoding=DEFAULT_ENCODING,
                errors="replace",
            )[:8000]

        except OSError:

            return None

        category = self._infer_category(file_path, content)
        tokens = self._tokenize(content)

        return IndexRecord(
            entry_id=f"file_{file_path.stem}_{abs(hash(str(file_path))) % 100000:05d}",
            title=file_path.name,
            category=category.value,
            document_type=doc_type.value,
            source_path=str(file_path.relative_to(workspace)),
            token_count=len(tokens),
            keywords=list(Counter(tokens).keys())[:50],
            vector=self._build_vector(tokens),
        )

    def _index_entry(self, entry: KnowledgeEntry) -> IndexRecord:

        tokens = self._tokenize(f"{entry.title} {entry.content}")

        return IndexRecord(
            entry_id=entry.id,
            title=entry.title,
            category=entry.category.value,
            document_type=entry.document_type.value,
            source_path=entry.source_path,
            token_count=len(tokens),
            keywords=list(Counter(tokens).keys())[:50],
            vector=self._build_vector(tokens),
        )

    @staticmethod
    def _infer_category(file_path: Path, content: str) -> KnowledgeCategory:

        lower_name = file_path.name.lower()
        lower_content = content.lower()

        if "prd" in lower_name:

            return KnowledgeCategory.PRD

        if "architecture" in lower_name or "architecture" in lower_content:

            return KnowledgeCategory.ARCHITECTURE

        if file_path.suffix.lower() in {".py", ".ts", ".js"}:

            return KnowledgeCategory.CODE_PATTERN

        if "api" in lower_name or "@app." in content or "router" in lower_content:

            return KnowledgeCategory.SOLUTION

        return KnowledgeCategory.BEST_PRACTICE

    @staticmethod
    def _tokenize(text: str) -> list[str]:

        return [
            token.lower()
            for token in re.findall(r"[a-zA-Z0-9_\u4e00-\u9fff]{2,}", text)
        ]

    @staticmethod
    def _build_vector(tokens: list[str]) -> dict[str, float]:

        counts = Counter(tokens)
        total = sum(counts.values()) or 1

        return {
            token: count / total
            for token, count in counts.most_common(100)
        }

    def _save_index(
        self,
        workspace: Path,
        records: list[IndexRecord],
    ) -> None:

        root = KnowledgeRepository._knowledge_root(workspace)
        root.mkdir(parents=True, exist_ok=True)

        data = [
            {
                "entry_id": r.entry_id,
                "title": r.title,
                "category": r.category,
                "document_type": r.document_type,
                "source_path": r.source_path,
                "token_count": r.token_count,
                "keywords": r.keywords,
                "vector": r.vector,
            }
            for r in records
        ]

        index_path = root / self.INDEX_FILE
        index_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding=DEFAULT_ENCODING,
        )

    def _index_path(self, workspace: str | Path) -> Path:

        return (
            KnowledgeRepository._knowledge_root(workspace)
            / self.INDEX_FILE
        )
