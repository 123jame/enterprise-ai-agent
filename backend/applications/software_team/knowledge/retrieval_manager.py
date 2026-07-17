from __future__ import annotations

import math
import re
from pathlib import Path

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.knowledge.document_indexer import DocumentIndexer
from applications.software_team.knowledge.knowledge_repository import KnowledgeRepository
from applications.software_team.knowledge.knowledge_result import IndexRecord
from applications.software_team.knowledge.knowledge_result import KnowledgeEntry
from applications.software_team.knowledge.knowledge_result import RetrievalHit
from applications.software_team.knowledge.knowledge_result import RetrievalMode
from applications.software_team.knowledge.knowledge_result import RetrievalResult


class RetrievalManager:
    """
    统一知识检索：Keyword / Embedding / Hybrid Search。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        repository: KnowledgeRepository | None = None,
        indexer: DocumentIndexer | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._repo = repository or KnowledgeRepository(settings=self._settings)
        self._indexer = indexer or DocumentIndexer(
            settings=self._settings,
            repository=self._repo,
        )

    def search(
        self,
        workspace: str | Path,
        query: str,
        *,
        mode: RetrievalMode | None = None,
        limit: int | None = None,
    ) -> RetrievalResult:

        search_mode = mode or RetrievalMode(
            self._settings.knowledge_retrieval_mode,
        )
        max_results = limit or self._settings.knowledge_max_retrieval_results

        workspace_path = Path(workspace).resolve()
        index_records = self._indexer.load_index(workspace_path)

        if not index_records:

            index_records = self._indexer.index_workspace(workspace_path)

        entries = self._repo.list_entries(workspace_path)
        entry_map = {e.id: e for e in entries}

        query_tokens = self._tokenize(query)

        if not query_tokens:

            return RetrievalResult(
                success=True,
                query=query,
                mode=search_mode,
                hits=[],
            )

        keyword_scores = self._keyword_search(index_records, query_tokens)
        embedding_scores = self._embedding_search(index_records, query_tokens)

        combined: dict[str, float] = {}

        for entry_id, score in keyword_scores.items():

            combined[entry_id] = score * (
                0.4 if search_mode == RetrievalMode.HYBRID else 1.0
            )

        for entry_id, score in embedding_scores.items():

            weight = (
                0.6
                if search_mode == RetrievalMode.HYBRID
                else 1.0
            )

            if search_mode == RetrievalMode.EMBEDDING:

                combined[entry_id] = score * weight

            else:

                combined[entry_id] = combined.get(entry_id, 0.0) + score * weight

        if search_mode == RetrievalMode.KEYWORD:

            combined = keyword_scores

        ranked = sorted(
            combined.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:max_results]

        hits: list[RetrievalHit] = []

        for entry_id, score in ranked:

            if score <= 0:

                continue

            entry = entry_map.get(entry_id)

            if entry is None:

                entry = self._record_to_entry(entry_id, index_records)

            if entry is None:

                continue

            hits.append(
                RetrievalHit(
                    entry=entry,
                    score=score,
                    match_type=search_mode.value,
                    snippet=entry.content[:200],
                )
            )

        return RetrievalResult(
            success=True,
            query=query,
            mode=search_mode,
            hits=hits,
        )

    @staticmethod
    def _keyword_search(
        records: list[IndexRecord],
        query_tokens: list[str],
    ) -> dict[str, float]:

        scores: dict[str, float] = {}

        for record in records:

            overlap = sum(
                1 for token in query_tokens if token in record.keywords
            )

            if overlap > 0:

                scores[record.entry_id] = overlap / len(query_tokens)

        return scores

    @staticmethod
    def _embedding_search(
        records: list[IndexRecord],
        query_tokens: list[str],
    ) -> dict[str, float]:

        query_vector: dict[str, float] = {}

        for token in query_tokens:

            query_vector[token] = query_vector.get(token, 0.0) + 1.0

        total = sum(query_vector.values()) or 1.0

        query_vector = {
            k: v / total for k, v in query_vector.items()
        }

        scores: dict[str, float] = {}

        for record in records:

            if not record.vector:

                continue

            scores[record.entry_id] = RetrievalManager._cosine_similarity(
                query_vector,
                record.vector,
            )

        return scores

    @staticmethod
    def _cosine_similarity(
        vec_a: dict[str, float],
        vec_b: dict[str, float],
    ) -> float:

        common = set(vec_a) & set(vec_b)

        if not common:

            return 0.0

        dot = sum(vec_a[k] * vec_b[k] for k in common)
        norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
        norm_b = math.sqrt(sum(v * v for v in vec_b.values()))

        if norm_a == 0 or norm_b == 0:

            return 0.0

        return dot / (norm_a * norm_b)

    @staticmethod
    def _record_to_entry(
        entry_id: str,
        records: list[IndexRecord],
    ) -> KnowledgeEntry | None:

        from applications.software_team.knowledge.knowledge_result import (
            DocumentType,
        )
        from applications.software_team.knowledge.knowledge_result import (
            KnowledgeCategory,
        )

        for record in records:

            if record.entry_id != entry_id:

                continue

            return KnowledgeEntry(
                id=record.entry_id,
                title=record.title,
                category=KnowledgeCategory(record.category),
                content=record.title,
                source_path=record.source_path,
                document_type=DocumentType(record.document_type),
            )

        return None

    @staticmethod
    def _tokenize(text: str) -> list[str]:

        return [
            token.lower()
            for token in re.findall(r"[a-zA-Z0-9_\u4e00-\u9fff]{2,}", text)
        ]
