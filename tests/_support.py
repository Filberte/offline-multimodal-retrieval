"""Week4 测试共享的轻量替身与样本构造器。"""

from __future__ import annotations

from pathlib import Path

from week3_embedding.backends import HashingTextBackend
from week3_embedding.engine import EmbeddingEngine
from week3_embedding.vector_store import DOCUMENT_METADATA_KEY
from week4_retrieval.models import SemanticCandidate, StoredRecord
from week4_retrieval.service import CoreRetrievalService


class CrossModalHashingBackend(HashingTextBackend):
    """模拟 MobileCLIP 文本编码器的第二向量空间。"""

    model_name = "cross-modal-test"
    space = "mobileclip-test-v1"


def make_record(
    item_id: str,
    document: str | None = None,
    *,
    space: str = "bert",
    **metadata,
) -> StoredRecord:
    """构造具有完整来源字段的稳定检索记录。"""

    base = {
        "document_id": f"doc-{item_id}",
        "file_name": f"{item_id}.txt",
        "source_path": f"C:/library/{item_id}.txt",
        "model_name": "model",
        "modality": "text",
        "content_type": "text/plain",
        "extension": "txt",
        "chunk_index": "0",
    }
    base.update(metadata)
    return StoredRecord(item_id, document if document is not None else f"text {item_id}", base, space)


def matches_where(metadata: dict, where: dict | None) -> bool:
    """执行测试所需的 Chroma 等值过滤子集。"""

    if not where:
        return True
    clauses = where.get("$and", [where])
    return all(
        str(metadata.get(key, "")) == str(expression.get("$eq", ""))
        for clause in clauses
        for key, expression in clause.items()
    )


class MemoryRepository:
    """按 Week4 仓储接口实现的内存替身。"""

    def __init__(self):
        self.store = self
        self.records = {}
        self.semantic_calls = []
        self.scan_calls = []

    def upsert(self, vectors):
        vectors = tuple(vectors)
        for vector in vectors:
            metadata = dict(vector.metadata)
            document = str(metadata.pop(DOCUMENT_METADATA_KEY, ""))
            metadata.update(
                {
                    "space": vector.space,
                    "model_name": vector.model_name,
                    "modality": vector.modality.value,
                }
            )
            self.records[(vector.space, vector.item_id)] = (
                StoredRecord(vector.item_id, document, metadata, vector.space),
                vector.values,
            )
        return len(vectors)

    def semantic_search(self, *, space, query_embedding, n_results, where=None):
        self.semantic_calls.append(
            {
                "space": space,
                "query_embedding": tuple(query_embedding),
                "n_results": n_results,
                "where": where,
            }
        )
        candidates = []
        for (record_space, _), (record, values) in self.records.items():
            if record_space != space or not matches_where(record.metadata, where):
                continue
            similarity = sum(a * b for a, b in zip(query_embedding, values))
            candidates.append(SemanticCandidate(record, similarity))
        candidates.sort(key=lambda item: (-item.similarity, item.record.item_id))
        return tuple(candidates[:n_results])

    def scan(self, *, space, where=None, limit=None):
        self.scan_calls.append({"space": space, "where": where, "limit": limit})
        records = [
            record
            for (record_space, _), (record, _) in self.records.items()
            if record_space == space and matches_where(record.metadata, where)
        ]
        records.sort(key=lambda item: item.item_id)
        return tuple(records[:limit] if limit else records)

    def delete(self, *, space, ids):
        for item_id in ids:
            self.records.pop((space, item_id), None)


def make_service(
    *,
    cross_modal: bool = False,
    batch_size: int = 2,
    candidate_multiplier: int = 5,
) -> tuple[CoreRetrievalService, MemoryRepository]:
    """构造使用确定性哈希嵌入的端到端服务。"""

    repository = MemoryRepository()
    engine = EmbeddingEngine(
        text_backend=HashingTextBackend(dimension=64),
        cross_modal_text_backend=(
            CrossModalHashingBackend(dimension=64) if cross_modal else None
        ),
    )
    service = CoreRetrievalService(
        engine=engine,
        repository=repository,
        batch_size=batch_size,
        candidate_multiplier=candidate_multiplier,
    )
    return service, repository


def write_text(path: Path, text: str) -> Path:
    """写入 UTF-8 测试文本并返回路径。"""

    path.write_text(text, encoding="utf-8")
    return path
