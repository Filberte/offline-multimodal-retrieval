"""跨关键词与多向量空间的确定性混合排序。"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from week4_retrieval.keyword import KeywordMatch
from week4_retrieval.models import RetrievalHit, SemanticCandidate, StoredRecord


class HybridRanker:
    """按空间归一化语义分数，再与 BM25 分数加权融合。"""

    # 汇集语义与关键词候选，归一化后生成稳定排序的检索结果。
    def rank(
        self,
        *,
        semantic: Iterable[SemanticCandidate],
        keyword: Iterable[KeywordMatch],
        semantic_weight: float,
        keyword_weight: float,
        top_k: int,
    ) -> tuple[RetrievalHit, ...]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        total_weight = semantic_weight + keyword_weight
        if semantic_weight < 0 or keyword_weight < 0 or total_weight <= 0:
            raise ValueError("invalid ranking weights")
        semantic_weight /= total_weight
        keyword_weight /= total_weight

        semantic_items = tuple(semantic)
        keyword_items = tuple(keyword)
        records: dict[tuple[str, str], StoredRecord] = {}
        raw_semantic: dict[tuple[str, str], float] = {}
        raw_keyword: dict[tuple[str, str], float] = {}

        # 空间是记录主键的一部分，防止不同模型集合中的同名记录冲突。
        for candidate in semantic_items:
            key = (candidate.record.space, candidate.record.item_id)
            records[key] = candidate.record
            raw_semantic[key] = max(raw_semantic.get(key, -1.0), candidate.similarity)
        for match in keyword_items:
            key = (match.record.space, match.record.item_id)
            records[key] = match.record
            raw_keyword[key] = max(raw_keyword.get(key, 0.0), match.score)

        normalized_semantic = _normalize_semantic_by_space(raw_semantic)
        normalized_keyword = _normalize_positive(raw_keyword)
        scored: list[RetrievalHit] = []
        for key, record in records.items():
            semantic_score = normalized_semantic.get(key, 0.0)
            keyword_score = normalized_keyword.get(key, 0.0)
            score = semantic_weight * semantic_score + keyword_weight * keyword_score
            scored.append(_to_hit(record, score, semantic_score, keyword_score))

        # 稳定次级排序保证同一索引、同一查询重复运行得到相同顺序。
        scored.sort(
            key=lambda hit: (
                -hit.score,
                -hit.semantic_score,
                -hit.keyword_score,
                hit.file_name.casefold(),
                hit.item_id,
            )
        )
        return tuple(scored[:top_k])


# 在各向量空间内部独立执行 min-max 归一化。
def _normalize_semantic_by_space(
    scores: dict[tuple[str, str], float],
) -> dict[tuple[str, str], float]:
    grouped: dict[str, dict[tuple[str, str], float]] = defaultdict(dict)
    for key, value in scores.items():
        grouped[key[0]][key] = value
    normalized: dict[tuple[str, str], float] = {}
    for group in grouped.values():
        values = tuple(group.values())
        low, high = min(values), max(values)
        for key, value in group.items():
            if high == low:
                normalized[key] = 1.0 if high > 0 else 0.0
            else:
                normalized[key] = (value - low) / (high - low)
    return normalized


# 按当前候选最大正分归一化关键词得分。
def _normalize_positive(scores: dict[tuple[str, str], float]) -> dict[tuple[str, str], float]:
    if not scores:
        return {}
    maximum = max(scores.values())
    if maximum <= 0:
        return {key: 0.0 for key in scores}
    return {key: max(0.0, value) / maximum for key, value in scores.items()}


# 将底层存储记录和融合分数映射为稳定公开结果契约。
def _to_hit(
    record: StoredRecord,
    score: float,
    semantic_score: float,
    keyword_score: float,
) -> RetrievalHit:
    metadata = dict(record.metadata)
    raw_chunk = metadata.get("chunk_index")
    try:
        chunk_index = None if raw_chunk in (None, "", "null") else int(raw_chunk)
    except (TypeError, ValueError):
        chunk_index = None
    # 结果正文保留足够的上下文，Week5 可按需进一步高亮或截断。
    text = record.document.strip()
    return RetrievalHit(
        item_id=record.item_id,
        document_id=record.document_id,
        text=text,
        score=round(score, 8),
        semantic_score=round(semantic_score, 8),
        keyword_score=round(keyword_score, 8),
        space=record.space,
        model_name=str(metadata.get("model_name", "")),
        modality=str(metadata.get("modality", "")),
        source_path=str(metadata.get("source_path", "")),
        file_name=str(metadata.get("file_name", "")),
        content_type=str(metadata.get("content_type", "")),
        chunk_index=chunk_index,
        metadata=metadata,
    )
