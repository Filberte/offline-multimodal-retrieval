"""保留 Week2 ParseResult/FileMetadata 契约的 Week3 适配器。"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from week3_embedding.chunking import chunk_text
from week3_embedding.models import EmbeddingInput, Modality


IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png"}


def inputs_from_parse_result(parse_result: Any, *, max_characters: int = 900, overlap: int = 120) -> tuple[EmbeddingInput, ...]:
    # 文档标识由路径、修改时间和大小共同生成，可检测文件版本变化。
    metadata = parse_result.metadata
    document_id = stable_document_id(metadata.path, metadata.modified_time_utc, metadata.size_bytes)
    # 完整保留 Week2 元数据和警告，供 Week4 过滤、展示和来源追踪。
    base_metadata = {
        "document_id": document_id,
        "source_path": metadata.path,
        "file_name": metadata.file_name,
        "extension": metadata.extension,
        "content_type": metadata.content_type,
        "size_bytes": metadata.size_bytes,
        "modified_time_utc": metadata.modified_time_utc,
        "week2_extra": dict(metadata.extra),
        "warnings": list(parse_result.warnings),
        "parser_version": "week2-reference",
    }
    if metadata.content_type in IMAGE_CONTENT_TYPES:
        # 图像不做文本分块，直接将源文件路径交给 MobileCLIP。
        return (
            EmbeddingInput(
                item_id=document_id,
                modality=Modality.IMAGE,
                image_path=metadata.path,
                metadata={**base_metadata, "chunk_index": None},
            ),
        )

    # 其他可解析文件按文本块转为多个嵌入输入。
    chunks = chunk_text(parse_result.text, max_characters=max_characters, overlap=overlap)
    return tuple(
        EmbeddingInput(
            item_id=f"{document_id}:chunk:{chunk.index}",
            modality=Modality.TEXT,
            text=chunk.text,
            metadata={
                **base_metadata,
                "chunk_index": chunk.index,
                "start_character": chunk.start_character,
                "end_character": chunk.end_character,
            },
        )
        for chunk in chunks
    )


def stable_document_id(path: str, modified_time_utc: str, size_bytes: int) -> str:
    # 截取 SHA-256 前 24 位，在可读长度与碰撞风险之间取得平衡。
    payload = f"{Path(path).resolve()}|{modified_time_utc}|{size_bytes}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:24]
