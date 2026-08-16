"""统一调度文本/图像嵌入，并提供可容错的批处理能力。"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable

from week3_embedding.backends import ImageBackend, TextBackend
from week3_embedding.models import (
    BatchEmbeddingResult,
    BatchFailure,
    EmbeddingInput,
    EmbeddingVector,
    Modality,
)


class EmbeddingEngine:
    # 通过依赖注入组合不同后端，保持上层调用接口稳定。
    def __init__(
        self,
        *,
        text_backend: TextBackend,
        image_backend: ImageBackend | None = None,
        cross_modal_text_backend: TextBackend | None = None,
    ) -> None:
        self.text_backend = text_backend
        self.image_backend = image_backend
        self.cross_modal_text_backend = cross_modal_text_backend

    def embed(self, item: EmbeddingInput, *, space: str = "default") -> EmbeddingVector:
        # 单条处理也执行统一校验，避免无效数据进入模型或向量库。
        item.validate()
        if item.modality is Modality.TEXT:
            backend = self._select_text_backend(space)
            values = backend.embed_texts([item.text or ""])[0]
        else:
            if self.image_backend is None:
                raise RuntimeError("image backend is not configured")
            backend = self.image_backend
            values = backend.embed_images([item.image_path or ""])[0]
        return EmbeddingVector(
            item_id=item.item_id,
            modality=item.modality,
            space=backend.space,
            model_name=backend.model_name,
            values=values,
            metadata=dict(item.metadata),
        )

    def embed_batch(
        self,
        items: Iterable[EmbeddingInput],
        *,
        space: str = "default",
        continue_on_error: bool = True,
    ) -> BatchEmbeddingResult:
        # 当前批次在入口处物化；大文件库由 streaming 模块负责有界切批。
        materialized = list(items)
        vectors: list[EmbeddingVector] = []
        failures: list[BatchFailure] = []
        grouped: dict[Modality, list[EmbeddingInput]] = defaultdict(list)
        for item in materialized:
            try:
                item.validate()
                grouped[item.modality].append(item)
            except (OSError, ValueError) as exc:
                # 默认记录单条失败并继续，保证坏文件不阻塞整个本地文件库。
                if not continue_on_error:
                    raise
                failures.append(BatchFailure(item.item_id, type(exc).__name__, str(exc)))

        for modality, group in grouped.items():
            try:
                # 相同模态合并调用后端，减少模型调用次数。
                if modality is Modality.TEXT:
                    backend = self._select_text_backend(space)
                    values = backend.embed_texts([item.text or "" for item in group])
                else:
                    if self.image_backend is None:
                        raise RuntimeError("image backend is not configured")
                    backend = self.image_backend
                    values = backend.embed_images([item.image_path or "" for item in group])
                for item, vector in zip(group, values):
                    vectors.append(
                        EmbeddingVector(
                            item.item_id,
                            item.modality,
                            backend.space,
                            backend.model_name,
                            vector,
                            dict(item.metadata),
                        )
                    )
            except Exception as exc:
                # 后端级异常关联到本组每条输入，便于定位和重试。
                if not continue_on_error:
                    raise
                failures.extend(BatchFailure(item.item_id, type(exc).__name__, str(exc)) for item in group)
        return BatchEmbeddingResult(tuple(vectors), tuple(failures))

    def _select_text_backend(self, space: str) -> TextBackend:
        # 默认文本空间使用 BERT；跨模态空间使用 MobileCLIP 文本编码器。
        if space in {"default", "text"}:
            return self.text_backend
        if space in {"cross_modal", "image"} and self.cross_modal_text_backend is not None:
            return self.cross_modal_text_backend
        raise ValueError(f"unsupported embedding space: {space}")
