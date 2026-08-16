"""Chroma 向量库与 Week4 检索层之间的适配器。"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from week3_embedding.models import EmbeddingVector
from week3_embedding.vector_store import ChromaVectorStore
from week4_retrieval.models import SemanticCandidate, StoredRecord


class ChromaRetrievalRepository:
    """复用 Week3 Chroma 存储契约并补充检索所需的扫描能力。"""

    # 保存 Week3 向量存储实例，作为全部持久化操作的唯一入口。
    def __init__(self, store: ChromaVectorStore) -> None:
        self.store = store

    # 按 Week3 EmbeddingVector 契约批量新增或更新向量。
    def upsert(self, vectors: Iterable[EmbeddingVector]) -> int:
        return self.store.upsert(vectors)

    # 在指定向量空间执行相似度查询，并转换 Chroma 距离为余弦相似度。
    def semantic_search(
        self,
        *,
        space: str,
        query_embedding: Sequence[float],
        n_results: int,
        where: Mapping[str, Any] | None = None,
    ) -> tuple[SemanticCandidate, ...]:
        payload = self.store.query(
            space=space,
            query_embedding=query_embedding,
            n_results=n_results,
            where=where,
        )
        ids = _first_query_row(payload.get("ids"))
        documents = _first_query_row(payload.get("documents"))
        metadatas = _first_query_row(payload.get("metadatas"))
        distances = _first_query_row(payload.get("distances"))
        candidates: list[SemanticCandidate] = []
        for index, item_id in enumerate(ids):
            metadata = dict(_safe_index(metadatas, index, {}) or {})
            document = str(_safe_index(documents, index, "") or "")
            distance = float(_safe_index(distances, index, 1.0))
            # Chroma cosine distance 为 1 - cosine similarity。
            similarity = max(-1.0, min(1.0, 1.0 - distance))
            candidates.append(
                SemanticCandidate(
                    StoredRecord(str(item_id), document, metadata, space),
                    similarity,
                )
            )
        return tuple(candidates)

    # 扫描指定空间的文档与元数据，供关键词索引和过滤逻辑使用。
    def scan(
        self,
        *,
        space: str,
        where: Mapping[str, Any] | None = None,
        limit: int | None = None,
    ) -> tuple[StoredRecord, ...]:
        # Week3 当前对外接口只负责向量写入/查询；这里集中封装 Chroma get，
        # 避免上层排序与 UI 代码依赖底层集合对象。
        dimension = self.store._dimensions.get(space)  # noqa: SLF001 - 兼容 Week3 适配器边界。
        if dimension is None:
            raise ValueError(f"unknown vector space: {space}")
        kwargs: dict[str, Any] = {"include": ["metadatas", "documents"]}
        if where:
            kwargs["where"] = dict(where)
        if limit is not None:
            if limit <= 0:
                raise ValueError("limit must be greater than zero")
            kwargs["limit"] = limit
        payload = self.store._collection(space, dimension).get(**kwargs)  # noqa: SLF001
        ids = list(payload.get("ids") or [])
        documents = list(payload.get("documents") or [])
        metadatas = list(payload.get("metadatas") or [])
        return tuple(
            StoredRecord(
                str(item_id),
                str(_safe_index(documents, index, "") or ""),
                dict(_safe_index(metadatas, index, {}) or {}),
                space,
            )
            for index, item_id in enumerate(ids)
        )

    # 从指定向量空间删除给定记录标识。
    def delete(self, *, space: str, ids: Sequence[str]) -> None:
        self.store.delete(space=space, ids=ids)


# 提取 Chroma 单查询响应的第一行，并兼容空字段。
def _first_query_row(value: Any) -> list[Any]:
    if not value:
        return []
    return list(value[0])


# 安全读取并行响应数组，字段缺失时返回默认值。
def _safe_index(values: Sequence[Any], index: int, default: Any) -> Any:
    return values[index] if index < len(values) else default
