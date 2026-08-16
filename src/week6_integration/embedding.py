"""为 Week 3 嵌入引擎增加内容级缓存和批量去重。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from week3_embedding.engine import EmbeddingEngine
from week3_embedding.models import (
    BatchEmbeddingResult,
    BatchFailure,
    EmbeddingInput,
    EmbeddingVector,
)
from week6_integration.cache import LruCache


@dataclass(frozen=True)
class _CachedVector:
    space: str
    model_name: str
    values: tuple[float, ...]


class CachedEmbeddingEngine:
    """保持 Week 3 接口兼容，同时避免重复推理。"""

    def __init__(self, engine: EmbeddingEngine, *, cache_size: int = 1024) -> None:
        self.engine = engine
        self.cache: LruCache[str, _CachedVector] = LruCache(cache_size)

    @property
    def text_backend(self):
        return self.engine.text_backend

    @property
    def image_backend(self):
        return self.engine.image_backend

    @property
    def cross_modal_text_backend(self):
        return self.engine.cross_modal_text_backend

    def embed(self, item: EmbeddingInput, *, space: str = "default") -> EmbeddingVector:
        item.validate()
        key = self._cache_key(item, space)
        cached = self.cache.get(key)
        if cached is None:
            vector = self.engine.embed(item, space=space)
            cached = _CachedVector(vector.space, vector.model_name, vector.values)
            self.cache.put(key, cached)
        return self._restore(item, cached)

    def embed_batch(
        self,
        items: Iterable[EmbeddingInput],
        *,
        space: str = "default",
        continue_on_error: bool = True,
    ) -> BatchEmbeddingResult:
        """复用命中项，只把唯一未命中内容交给底层批处理。"""

        materialized = list(items)
        vectors_by_position: dict[int, EmbeddingVector] = {}
        failures: list[BatchFailure] = []
        misses: list[EmbeddingInput] = []
        miss_positions: list[int] = []
        representative_by_key: dict[str, int] = {}
        duplicate_positions: dict[int, list[int]] = {}

        for position, item in enumerate(materialized):
            try:
                item.validate()
            except (OSError, ValueError) as exc:
                if not continue_on_error:
                    raise
                failures.append(BatchFailure(item.item_id, type(exc).__name__, str(exc)))
                continue
            key = self._cache_key(item, space)
            cached = self.cache.get(key)
            if cached is not None:
                vectors_by_position[position] = self._restore(item, cached)
                continue
            if key in representative_by_key:
                duplicate_positions.setdefault(representative_by_key[key], []).append(position)
                continue
            representative_by_key[key] = position
            misses.append(item)
            miss_positions.append(position)

        if misses:
            result = self.engine.embed_batch(
                misses,
                space=space,
                continue_on_error=continue_on_error,
            )
            failures.extend(result.failures)
            output_by_id = {vector.item_id: vector for vector in result.vectors}
            for position, item in zip(miss_positions, misses):
                vector = output_by_id.get(item.item_id)
                if vector is None:
                    continue
                cached = _CachedVector(vector.space, vector.model_name, vector.values)
                self.cache.put(self._cache_key(item, space), cached)
                vectors_by_position[position] = self._restore(item, cached)
                for duplicate_position in duplicate_positions.get(position, []):
                    duplicate = materialized[duplicate_position]
                    vectors_by_position[duplicate_position] = self._restore(duplicate, cached)

        vectors = tuple(vectors_by_position[index] for index in sorted(vectors_by_position))
        return BatchEmbeddingResult(vectors=vectors, failures=tuple(failures))

    @staticmethod
    def _restore(item: EmbeddingInput, cached: _CachedVector) -> EmbeddingVector:
        return EmbeddingVector(
            item_id=item.item_id,
            modality=item.modality,
            space=cached.space,
            model_name=cached.model_name,
            values=cached.values,
            metadata=dict(item.metadata),
        )

    @staticmethod
    def _cache_key(item: EmbeddingInput, space: str) -> str:
        if item.text is not None:
            content = item.text.strip()
        else:
            path = Path(item.image_path or "")
            try:
                stat = path.stat()
                content = f"{path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}"
            except OSError:
                content = str(path)
        raw = f"{item.modality.value}|{space}|{content}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
