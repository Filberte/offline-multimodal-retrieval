"""Week4 本地向量存储与混合检索模块公开 API。"""

from week4_retrieval.keyword import BM25Index, KeywordMatch, tokenize
from week4_retrieval.metrics import BenchmarkCase, BenchmarkResult, evaluate_retrieval
from week4_retrieval.models import (
    IndexingSummary,
    RetrievalHit,
    SearchFilters,
    SearchQuery,
    SearchResponse,
    SemanticCandidate,
    StoredRecord,
)
from week4_retrieval.ranking import HybridRanker
from week4_retrieval.repository import ChromaRetrievalRepository
from week4_retrieval.service import CoreRetrievalService

# 集中导出稳定的核心检索接口，供命令行、Flutter 客户端适配层和测试代码复用。
__all__ = [
    "BM25Index",
    "BenchmarkCase",
    "BenchmarkResult",
    "ChromaRetrievalRepository",
    "CoreRetrievalService",
    "HybridRanker",
    "IndexingSummary",
    "KeywordMatch",
    "RetrievalHit",
    "SearchFilters",
    "SearchQuery",
    "SearchResponse",
    "SemanticCandidate",
    "StoredRecord",
    "evaluate_retrieval",
    "tokenize",
]
