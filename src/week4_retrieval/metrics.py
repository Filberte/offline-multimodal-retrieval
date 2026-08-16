"""检索准确率与时延基准计算。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Sequence

from week4_retrieval.models import SearchQuery
from week4_retrieval.service import CoreRetrievalService


@dataclass(frozen=True)
class BenchmarkCase:
    """一个查询及其相关文档/记录标识集合。"""

    case_id: str
    query: str
    relevant_ids: frozenset[str]


@dataclass(frozen=True)
class BenchmarkResult:
    case_count: int
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    mrr_at_10: float
    ndcg_at_10: float
    mean_latency_ms: float
    p95_latency_ms: float

    # 转换为可直接写入 JSON 报告的基础类型字典。
    def to_dict(self) -> dict[str, float | int]:
        return self.__dict__.copy()


# 对一组带相关性标注的查询计算召回率、MRR、nDCG 与时延指标。
def evaluate_retrieval(
    service: CoreRetrievalService,
    cases: Iterable[BenchmarkCase],
    *,
    top_k: int = 10,
) -> BenchmarkResult:
    materialized = tuple(cases)
    if not materialized:
        raise ValueError("benchmark requires at least one case")
    reciprocal_ranks: list[float] = []
    ndcgs: list[float] = []
    latencies: list[float] = []
    recalls = {1: [], 5: [], 10: []}

    for case in materialized:
        if not case.relevant_ids:
            raise ValueError(f"case {case.case_id} has no relevant ids")
        response = service.search(SearchQuery(case.query, top_k=top_k, include_cross_modal=False))
        ranked_ids = [
            identifier
            for hit in response.hits
            for identifier in ({hit.item_id, hit.document_id},)
        ]
        # 每个名次只判断一次，兼容以 chunk id 或 document id 标注的基准。
        relevance = [
            bool(set(identifiers) & set(case.relevant_ids))
            for identifiers in ranked_ids
        ]
        first_rank = next((index + 1 for index, matched in enumerate(relevance) if matched), None)
        reciprocal_ranks.append(0.0 if first_rank is None else 1.0 / first_rank)
        for cutoff in recalls:
            recalls[cutoff].append(1.0 if any(relevance[:cutoff]) else 0.0)
        ndcgs.append(_binary_ndcg(relevance[:10], min(len(case.relevant_ids), 10)))
        latencies.append(response.elapsed_ms)

    return BenchmarkResult(
        case_count=len(materialized),
        recall_at_1=round(mean(recalls[1]), 6),
        recall_at_5=round(mean(recalls[5]), 6),
        recall_at_10=round(mean(recalls[10]), 6),
        mrr_at_10=round(mean(reciprocal_ranks), 6),
        ndcg_at_10=round(mean(ndcgs), 6),
        mean_latency_ms=round(mean(latencies), 3),
        p95_latency_ms=round(_percentile(latencies, 0.95), 3),
    )


# 按二元相关性计算指定结果序列的归一化折损累计增益。
def _binary_ndcg(relevance: Sequence[bool], ideal_relevant: int) -> float:
    dcg = sum((1.0 if matched else 0.0) / math.log2(index + 2) for index, matched in enumerate(relevance))
    ideal = sum(1.0 / math.log2(index + 2) for index in range(min(ideal_relevant, len(relevance))))
    return 0.0 if ideal == 0 else dcg / ideal


# 使用线性插值计算时延样本的指定分位数。
def _percentile(values: Sequence[float], quantile: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction
