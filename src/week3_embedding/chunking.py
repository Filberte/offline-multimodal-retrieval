"""连接 Week2 文件解析与 Week3 嵌入处理的确定性文本分块模块。"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    # 字符偏移量用于 Week4 检索结果回溯到原始文档位置。
    index: int
    text: str
    start_character: int
    end_character: int


def chunk_text(text: str, *, max_characters: int = 900, overlap: int = 120) -> tuple[TextChunk, ...]:
    # 先归一化空白字符，保证跨 TXT、PDF、DOCX 输入得到一致分块。
    if max_characters <= 0:
        raise ValueError("max_characters must be positive")
    if overlap < 0 or overlap >= max_characters:
        raise ValueError("overlap must be in [0, max_characters)")
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return ()

    chunks: list[TextChunk] = []
    start = 0
    while start < len(cleaned):
        hard_end = min(start + max_characters, len(cleaned))
        end = hard_end
        if hard_end < len(cleaned):
            # 优先在后半段的空格处断开，降低词语被截断的概率。
            boundary = cleaned.rfind(" ", start + max_characters // 2, hard_end)
            if boundary > start:
                end = boundary
        chunk = cleaned[start:end].strip()
        if chunk:
            actual_start = cleaned.find(chunk, start, end + 1)
            chunks.append(TextChunk(len(chunks), chunk, actual_start, actual_start + len(chunk)))
        if end >= len(cleaned):
            break
        # 保留上下文重叠，同时强制游标前进以避免极端输入导致死循环。
        start = max(end - overlap, start + 1)
    return tuple(chunks)
