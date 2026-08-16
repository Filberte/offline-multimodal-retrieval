"""Week4 检索层公开的数据契约。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class SearchFilters:
    """可由 Week5 UI 直接映射的检索过滤条件。"""

    modality: str | None = None
    content_type: str | None = None
    extension: str | None = None
    document_id: str | None = None
    source_path_contains: str | None = None

    # 将可精确匹配的字段转换为 Chroma where 查询表达式。
    def to_chroma_where(self) -> dict[str, Any] | None:
        # Chroma 只处理精确过滤；路径包含过滤在召回后执行。
        clauses: list[dict[str, Any]] = []
        for key in ("modality", "content_type", "extension", "document_id"):
            value = getattr(self, key)
            if value:
                clauses.append({key: {"$eq": value}})
        if not clauses:
            return None
        return clauses[0] if len(clauses) == 1 else {"$and": clauses}

    # 对召回结果执行统一二次校验，并处理路径包含条件。
    def accepts(self, metadata: Mapping[str, Any]) -> bool:
        # 二次校验保证不同 Chroma 版本的过滤行为一致。
        for key in ("modality", "content_type", "extension", "document_id"):
            expected = getattr(self, key)
            if expected and str(metadata.get(key, "")) != expected:
                return False
        if self.source_path_contains:
            needle = self.source_path_contains.casefold()
            if needle not in str(metadata.get("source_path", "")).casefold():
                return False
        return True


@dataclass(frozen=True)
class SearchQuery:
    """混合检索请求；默认以语义分数为主、关键词分数为辅。"""

    text: str
    top_k: int = 10
    semantic_weight: float = 0.70
    keyword_weight: float = 0.30
    include_cross_modal: bool = True
    filters: SearchFilters = field(default_factory=SearchFilters)

    # 校验查询文本、返回数量和混合排序权重的业务约束。
    def validate(self) -> None:
        if not self.text.strip():
            raise ValueError("query text must not be blank")
        if self.top_k <= 0 or self.top_k > 100:
            raise ValueError("top_k must be between 1 and 100")
        if self.semantic_weight < 0 or self.keyword_weight < 0:
            raise ValueError("ranking weights must not be negative")
        if self.semantic_weight + self.keyword_weight <= 0:
            raise ValueError("at least one ranking weight must be positive")


@dataclass(frozen=True)
class StoredRecord:
    """从 Chroma 读取的原始记录。"""

    item_id: str
    document: str
    metadata: dict[str, Any]
    space: str

    @property
    # 优先返回来源文档标识，缺失时回退到记录标识。
    def document_id(self) -> str:
        return str(self.metadata.get("document_id", self.item_id))


@dataclass(frozen=True)
class SemanticCandidate:
    """单一向量空间中的语义召回候选。"""

    record: StoredRecord
    similarity: float


@dataclass(frozen=True)
class RetrievalHit:
    """面向 UI 与 API 的稳定检索结果。"""

    item_id: str
    document_id: str
    text: str
    score: float
    semantic_score: float
    keyword_score: float
    space: str
    model_name: str
    modality: str
    source_path: str
    file_name: str
    content_type: str
    chunk_index: int | None
    metadata: dict[str, Any] = field(default_factory=dict)

    # 将单条检索结果递归转换为可序列化字典。
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SearchResponse:
    """一次检索的完整响应与可观测信息。"""

    query: str
    hits: tuple[RetrievalHit, ...]
    elapsed_ms: float
    candidate_count: int
    warnings: tuple[str, ...] = ()

    # 将完整检索响应转换为 JSON 兼容结构。
    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "hits": [hit.to_dict() for hit in self.hits],
            "elapsed_ms": self.elapsed_ms,
            "candidate_count": self.candidate_count,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class IndexingSummary:
    """端到端索引任务的成功、失败与写入统计。"""

    discovered_files: int
    parsed_files: int
    parse_failures: tuple[dict[str, str], ...]
    embedding_inputs: int
    embedding_failures: tuple[dict[str, str], ...]
    persisted_vectors: int

    @property
    # 仅在解析和嵌入阶段均无失败时标记索引任务成功。
    def success(self) -> bool:
        return not self.parse_failures and not self.embedding_failures
