"""面向大型本地文件库的有界批量嵌入调度。"""

from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import islice
from typing import Iterable, Iterator

from week3_embedding.engine import EmbeddingEngine
from week3_embedding.models import BatchEmbeddingResult, EmbeddingInput, Modality
from week3_embedding.vector_store import ChromaVectorStore, DOCUMENT_METADATA_KEY


@dataclass(frozen=True)
class PersistedEmbeddingBatch:
    # 同时报告本批处理结果和实际写入向量库的数量。
    result: BatchEmbeddingResult
    persisted_vectors: int = 0


class BoundedEmbeddingPipeline:
    """按固定大小窗口完成嵌入，并可选择立即持久化。"""

    def __init__(
        self,
        engine: EmbeddingEngine,
        *,
        store: ChromaVectorStore | None = None,
        batch_size: int = 32,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")
        self.engine = engine
        self.store = store
        self.batch_size = batch_size

    def iter_batches(
        self,
        items: Iterable[EmbeddingInput],
        *,
        space: str = "default",
        continue_on_error: bool = True,
    ) -> Iterator[PersistedEmbeddingBatch]:
        # islice 每次最多读取 batch_size 条，避免一次性加载整个文件库。
        iterator = iter(items)
        while batch := tuple(islice(iterator, self.batch_size)):
            result = self.engine.embed_batch(
                batch,
                space=space,
                continue_on_error=continue_on_error,
            )
            persisted = 0
            if self.store is not None and result.vectors:
                # 将原始文本写入 Chroma documents 字段，支持 Week4 结果展示。
                source_by_id = {item.item_id: item for item in batch}
                enriched = []
                for vector in result.vectors:
                    source = source_by_id.get(vector.item_id)
                    metadata = dict(vector.metadata)
                    if source is not None and source.modality is Modality.TEXT:
                        metadata[DOCUMENT_METADATA_KEY] = source.text or ""
                    enriched.append(replace(vector, metadata=metadata))
                persisted = self.store.upsert(enriched)
            # 逐批 yield，使调用方可实时展示进度或执行取消操作。
            yield PersistedEmbeddingBatch(result=result, persisted_vectors=persisted)

