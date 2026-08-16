"""Week 6 运行状态、性能与安全审查数据契约。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CacheStats:
    """LRU 缓存的容量和命中统计。"""

    hits: int
    misses: int
    evictions: int
    size: int
    capacity: int

    @property
    def requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        return self.hits / self.requests if self.requests else 0.0

    def to_dict(self) -> dict[str, int | float]:
        payload = asdict(self)
        payload["requests"] = self.requests
        payload["hit_rate"] = round(self.hit_rate, 6)
        return payload


@dataclass(frozen=True)
class RuntimeMetrics:
    """索引与检索服务的轻量运行指标。"""

    index_operations: int
    indexed_files: int
    persisted_vectors: int
    search_operations: int
    search_cache_hits: int
    search_failures: int
    total_search_ms: float

    @property
    def average_search_ms(self) -> float:
        if not self.search_operations:
            return 0.0
        return self.total_search_ms / self.search_operations

    def to_dict(self) -> dict[str, int | float]:
        payload = asdict(self)
        payload["average_search_ms"] = round(self.average_search_ms, 3)
        payload["total_search_ms"] = round(self.total_search_ms, 3)
        return payload


@dataclass(frozen=True)
class BackendHealth:
    """提供给 Flutter UI 的本地后端健康状态。"""

    status: str
    mode: str
    offline_only: bool
    backend_name: str
    vector_store: str
    indexed_records: int
    uptime_seconds: float
    embedding_cache: CacheStats
    query_cache: CacheStats
    metrics: RuntimeMetrics
    issues: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return self.status == "ready"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mode": self.mode,
            "offline_only": self.offline_only,
            "backend_name": self.backend_name,
            "vector_store": self.vector_store,
            "indexed_records": self.indexed_records,
            "uptime_seconds": round(self.uptime_seconds, 3),
            "embedding_cache": self.embedding_cache.to_dict(),
            "query_cache": self.query_cache.to_dict(),
            "metrics": self.metrics.to_dict(),
            "issues": list(self.issues),
        }


@dataclass(frozen=True)
class SecurityFinding:
    """单条静态安全审查发现。"""

    code: str
    severity: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class SecurityReview:
    """本地数据、凭据和外部端点的审查汇总。"""

    scanned_files: int
    findings: tuple[SecurityFinding, ...]
    offline_only: bool = True

    @property
    def critical_findings(self) -> int:
        return sum(item.severity == "critical" for item in self.findings)

    @property
    def high_findings(self) -> int:
        return sum(item.severity == "high" for item in self.findings)

    @property
    def passed(self) -> bool:
        return self.offline_only and not (self.critical_findings or self.high_findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scanned_files": self.scanned_files,
            "offline_only": self.offline_only,
            "critical_findings": self.critical_findings,
            "high_findings": self.high_findings,
            "passed": self.passed,
            "findings": [item.to_dict() for item in self.findings],
        }
