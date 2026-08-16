"""面向 Week4 的 Week3 向量持久化 Chroma 适配器。"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from week3_embedding.models import EmbeddingVector


DEFAULT_COLLECTIONS = {
    "bert-base-mean-pool-v1": "week4_text_bert_v1",
    "mobileclip-s1-shared-v1": "week4_cross_modal_mobileclip_v1",
}
DEFAULT_DIMENSIONS = {
    "bert-base-mean-pool-v1": 768,
    "mobileclip-s1-shared-v1": 512,
}
SCHEMA_VERSION = "week4-vector-record-v1"
DOCUMENT_METADATA_KEY = "_chroma_document"


class ChromaVectorStore:
    """在严格隔离不同向量空间的前提下完成持久化与查询。"""

    def __init__(
        self,
        persist_directory: str | Path,
        *,
        client: Any | None = None,
        collection_names: Mapping[str, str] | None = None,
        expected_dimensions: Mapping[str, int] | None = None,
    ) -> None:
        self.persist_directory = Path(persist_directory)
        self._client = client
        self._collection_names = {**DEFAULT_COLLECTIONS, **(collection_names or {})}
        self._dimensions = {**DEFAULT_DIMENSIONS, **(expected_dimensions or {})}
        self._collections: dict[str, Any] = {}

    def upsert(self, vectors: Iterable[EmbeddingVector]) -> int:
        # 先按向量空间分组，禁止 BERT 与 MobileCLIP 向量混入同一集合。
        grouped: dict[str, list[EmbeddingVector]] = defaultdict(list)
        for vector in vectors:
            self._validate_vector(vector)
            grouped[vector.space].append(vector)
        written = 0
        for space, group in grouped.items():
            collection = self._collection(space, group[0].dimension)
            records = [vector_to_chroma_record(vector) for vector in group]
            collection.upsert(
                ids=[record["id"] for record in records],
                embeddings=[record["embedding"] for record in records],
                metadatas=[record["metadata"] for record in records],
                documents=[record["document"] for record in records],
            )
            written += len(records)
        return written

    def query(
        self,
        *,
        space: str,
        query_embedding: Sequence[float],
        n_results: int = 10,
        where: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if n_results <= 0:
            raise ValueError("n_results must be greater than zero")
        # 查询前执行维度和有限数校验，尽早阻止损坏向量进入 Chroma。
        values = tuple(float(value) for value in query_embedding)
        self._validate_dimension(space, len(values))
        if not values or not all(math.isfinite(value) for value in values):
            raise ValueError("query_embedding must contain finite values")
        kwargs: dict[str, Any] = {
            "query_embeddings": [list(values)],
            "n_results": n_results,
            "include": ["metadatas", "documents", "distances"],
        }
        if where:
            kwargs["where"] = dict(where)
        return self._collection(space, len(values)).query(**kwargs)

    def delete(self, *, space: str, ids: Sequence[str]) -> None:
        # 空列表按幂等操作处理，避免无意义访问数据库。
        if not ids:
            return
        dimension = self._dimensions.get(space)
        if dimension is None:
            raise ValueError(f"unknown vector space: {space}")
        self._collection(space, dimension).delete(ids=list(ids))

    def _validate_vector(self, vector: EmbeddingVector) -> None:
        if not vector.item_id.strip():
            raise ValueError("vector item_id must not be empty")
        if not vector.values or not all(math.isfinite(value) for value in vector.values):
            raise ValueError("embedding must contain finite values")
        self._validate_dimension(vector.space, vector.dimension)

    def _validate_dimension(self, space: str, dimension: int) -> None:
        # 首次出现的新空间会锁定维度，后续维度漂移立即报错。
        if dimension <= 0:
            raise ValueError("embedding dimension must be greater than zero")
        expected = self._dimensions.setdefault(space, dimension)
        if expected != dimension:
            raise ValueError(
                f"vector space {space!r} expects {expected} dimensions, got {dimension}"
            )

    def _collection(self, space: str, dimension: int) -> Any:
        # 缓存集合对象，减少重复创建和数据库元数据查询。
        if space in self._collections:
            return self._collections[space]
        self._validate_dimension(space, dimension)
        if self._client is None:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            try:
                # Chroma 仅在首次真实访问时加载，保持模块导入轻量。
                import chromadb
            except ImportError as exc:
                raise RuntimeError(
                    "Install chromadb or use the unified project environment"
                ) from exc
            self._client = chromadb.PersistentClient(path=str(self.persist_directory))
        name = self._collection_names.get(space, _safe_collection_name(space))
        collection = self._client.get_or_create_collection(
            name=name,
            metadata={
                "hnsw:space": "cosine",
                "vector_space": space,
                "schema_version": SCHEMA_VERSION,
                "dimension": int(self._dimensions[space]),
            },
        )
        self._collections[space] = collection
        return collection


def vector_to_chroma_record(vector: EmbeddingVector) -> dict[str, Any]:
    # Chroma 的 document 字段与 metadata 分开保存，便于返回原文片段。
    source_metadata = dict(vector.metadata)
    document = str(source_metadata.pop(DOCUMENT_METADATA_KEY, ""))
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "space": vector.space,
        "model_name": vector.model_name,
        "modality": vector.modality.value,
        **source_metadata,
    }
    return {
        "id": vector.item_id,
        "embedding": [float(value) for value in vector.values],
        "metadata": _flatten_metadata(metadata),
        "document": document,
    }


def _flatten_metadata(metadata: Mapping[str, Any]) -> dict[str, str | int | float | bool]:
    # Chroma 只接受标量元数据，嵌套对象统一序列化为稳定 JSON 字符串。
    flattened: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        name = str(key)
        if isinstance(value, (str, int, bool)):
            flattened[name] = value
        elif isinstance(value, float) and math.isfinite(value):
            flattened[name] = value
        elif isinstance(value, (dict, list, tuple)):
            flattened[name] = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            flattened[name] = str(value)
    return flattened


def _safe_collection_name(space: str) -> str:
    # 清洗名称并附加哈希，兼顾 Chroma 命名规则和空间唯一性。
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", space).strip("-_").lower()
    digest = hashlib.sha1(space.encode("utf-8")).hexdigest()[:8]
    base = normalized[:48] or "vector-space"
    return f"week4-{base}-{digest}"

