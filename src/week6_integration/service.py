"""面向桌面 UI 的稳定集成检索服务。"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
from pathlib import Path
from threading import RLock
from time import perf_counter
from typing import Iterable, Iterator, Sequence

from week4_retrieval.models import IndexingSummary, SearchQuery, SearchResponse
from week4_retrieval.service import CoreRetrievalService
from week6_integration.cache import LruCache
from week6_integration.models import BackendHealth, RuntimeMetrics

_SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx", ".jpg", ".jpeg", ".png"}


@dataclass
class _MutableMetrics:
    index_operations: int = 0
    indexed_files: int = 0
    persisted_vectors: int = 0
    search_operations: int = 0
    search_cache_hits: int = 0
    search_failures: int = 0
    total_search_ms: float = 0.0

    def snapshot(self) -> RuntimeMetrics:
        return RuntimeMetrics(
            index_operations=self.index_operations,
            indexed_files=self.indexed_files,
            persisted_vectors=self.persisted_vectors,
            search_operations=self.search_operations,
            search_cache_hits=self.search_cache_hits,
            search_failures=self.search_failures,
            total_search_ms=self.total_search_ms,
        )


class IntegratedRetrievalService:
    """组合索引、检索、缓存、运行指标和健康检查。"""

    def __init__(
        self,
        core: CoreRetrievalService,
        *,
        query_cache_size: int = 256,
        file_batch_size: int = 64,
    ) -> None:
        if file_batch_size <= 0:
            raise ValueError("file_batch_size must be greater than zero")
        self.core = core
        self.file_batch_size = file_batch_size
        self.query_cache: LruCache[tuple[object, ...], SearchResponse] = LruCache(
            query_cache_size
        )
        self._metrics = _MutableMetrics()
        self._started = perf_counter()
        self._lock = RLock()

    def index_paths(
        self,
        paths: Iterable[str | Path],
        *,
        continue_on_error: bool = True,
    ) -> IndexingSummary:
        """按稳定接口写入一组路径，并使旧查询缓存失效。"""

        materialized = tuple(Path(path) for path in paths)
        with self._lock:
            summary = self.core.index_paths(
                materialized,
                continue_on_error=continue_on_error,
            )
            self._record_index(summary)
            self.query_cache.clear()
            return summary

    def index_directory(
        self,
        root: str | Path,
        *,
        recursive: bool = True,
        continue_on_error: bool = True,
    ) -> IndexingSummary:
        """以固定文件窗口扫描大型目录，限制一次性内存占用。"""

        iterator = self._iter_supported_files(Path(root), recursive=recursive)
        summaries: list[IndexingSummary] = []
        with self._lock:
            while batch := tuple(islice(iterator, self.file_batch_size)):
                summaries.append(
                    self.core.index_paths(batch, continue_on_error=continue_on_error)
                )
            summary = self._merge_summaries(summaries)
            self._record_index(summary)
            self.query_cache.clear()
            return summary

    def search(self, request: SearchQuery) -> SearchResponse:
        """执行带结果缓存的混合检索，并持续记录延迟与失败。"""

        request.validate()
        started = perf_counter()
        key = self._query_key(request)
        cached = self.query_cache.get(key)
        cache_hit = cached is not None
        try:
            if cached is None:
                response = self.core.search(request)
                self.query_cache.put(key, response)
            else:
                response = cached
            elapsed_ms = (perf_counter() - started) * 1000
            result = SearchResponse(
                query=response.query,
                hits=response.hits,
                elapsed_ms=round(elapsed_ms if cache_hit else response.elapsed_ms, 3),
                candidate_count=response.candidate_count,
                warnings=response.warnings,
            )
        except Exception:
            with self._lock:
                self._metrics.search_failures += 1
            raise
        with self._lock:
            self._metrics.search_operations += 1
            self._metrics.search_cache_hits += int(cache_hit)
            self._metrics.total_search_ms += result.elapsed_ms
        return result

    def library_items(self, spaces: Sequence[str] | None = None) -> tuple[dict, ...]:
        """从向量库读取并按文档标识去重，供资料库页面展示。"""

        if spaces is None:
            spaces = self._known_spaces()
        documents: dict[str, dict] = {}
        for space in spaces:
            try:
                records = self.core.repository.scan(space=space)
            except (RuntimeError, ValueError):
                continue
            for record in records:
                document_id = record.document_id
                if document_id in documents:
                    continue
                metadata = record.metadata
                documents[document_id] = {
                    "item_id": record.item_id,
                    "document_id": document_id,
                    "text": record.document,
                    "score": 0.0,
                    "semantic_score": 0.0,
                    "keyword_score": 0.0,
                    "space": record.space,
                    "modality": str(metadata.get("modality", "text")),
                    "source_path": str(metadata.get("source_path", "")),
                    "file_name": str(metadata.get("file_name", record.item_id)),
                    "content_type": str(metadata.get("content_type", "")),
                    "chunk_index": self._optional_int(metadata.get("chunk_index")),
                    "metadata": dict(metadata),
                }
        return tuple(
            sorted(
                documents.values(),
                key=lambda item: (str(item["file_name"]).casefold(), str(item["item_id"])),
            )
        )

    def health(self, *, issues: Iterable[str] = ()) -> BackendHealth:
        """返回 UI 可直接显示的离线后端健康状态。"""

        issue_tuple = tuple(issues)
        metrics = self.metrics
        engine = self.core.engine
        embedding_cache = getattr(engine, "cache", None)
        cache_stats = embedding_cache.stats if embedding_cache is not None else self.query_cache.stats
        return BackendHealth(
            status="degraded" if issue_tuple else "ready",
            mode="integrated-local",
            offline_only=True,
            backend_name=getattr(engine.text_backend, "model_name", type(engine).__name__),
            vector_store=type(self.core.repository.store).__name__,
            indexed_records=metrics.persisted_vectors,
            uptime_seconds=perf_counter() - self._started,
            embedding_cache=cache_stats,
            query_cache=self.query_cache.stats,
            metrics=metrics,
            issues=issue_tuple,
        )

    @property
    def metrics(self) -> RuntimeMetrics:
        with self._lock:
            return self._metrics.snapshot()

    def _record_index(self, summary: IndexingSummary) -> None:
        self._metrics.index_operations += 1
        self._metrics.indexed_files += summary.parsed_files
        self._metrics.persisted_vectors += summary.persisted_vectors

    def _known_spaces(self) -> tuple[str, ...]:
        engine = self.core.engine
        candidates = [getattr(engine.text_backend, "space", "")]
        if engine.image_backend is not None:
            candidates.append(getattr(engine.image_backend, "space", ""))
        return tuple(dict.fromkeys(space for space in candidates if space))

    @staticmethod
    def _iter_supported_files(root: Path, *, recursive: bool) -> Iterator[Path]:
        pattern = "**/*" if recursive else "*"
        for path in root.glob(pattern):
            if path.is_file() and path.suffix.casefold() in _SUPPORTED_EXTENSIONS:
                yield path

    @staticmethod
    def _merge_summaries(summaries: Sequence[IndexingSummary]) -> IndexingSummary:
        return IndexingSummary(
            discovered_files=sum(item.discovered_files for item in summaries),
            parsed_files=sum(item.parsed_files for item in summaries),
            parse_failures=tuple(
                failure for item in summaries for failure in item.parse_failures
            ),
            embedding_inputs=sum(item.embedding_inputs for item in summaries),
            embedding_failures=tuple(
                failure for item in summaries for failure in item.embedding_failures
            ),
            persisted_vectors=sum(item.persisted_vectors for item in summaries),
        )

    @staticmethod
    def _query_key(request: SearchQuery) -> tuple[object, ...]:
        filters = request.filters
        return (
            request.text.strip().casefold(),
            request.top_k,
            round(request.semantic_weight, 8),
            round(request.keyword_weight, 8),
            request.include_cross_modal,
            filters.modality,
            filters.content_type,
            filters.extension,
            filters.document_id,
            filters.source_path_contains,
        )

    @staticmethod
    def _optional_int(value: object) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
