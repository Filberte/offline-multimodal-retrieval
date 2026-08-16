"""文件解析和批量导入共享的数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FileMetadata:
    """每个导入文件都会生成的标准化元数据。"""

    path: str
    file_name: str
    extension: str
    size_bytes: int
    modified_time_utc: str
    content_type: str
    # extra 用来承载不同格式的专属信息，例如 PDF 页数、图片宽高、DOCX 段落数。
    # 这样可以保持主字段稳定，同时给后续功能留扩展空间。
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_path(
        cls,
        path: Path,
        *,
        content_type: str,
        extra: dict[str, Any] | None = None,
    ) -> "FileMetadata":
        # 统一从文件系统读取大小和修改时间，保证所有格式的基础元数据一致。
        stat = path.stat()
        return cls(
            path=str(path.resolve()),
            file_name=path.name,
            extension=path.suffix.lower().lstrip("."),
            size_bytes=stat.st_size,
            modified_time_utc=_format_timestamp(stat.st_mtime),
            content_type=content_type,
            extra=extra or {},
        )


@dataclass(frozen=True)
class ParseResult:
    """单个文件的解析文本、元数据和非致命警告。"""

    metadata: FileMetadata
    text: str
    # warnings 记录非致命问题，例如“PDF 没有可提取文本”。
    # 这类信息后续可在 UI 中提示用户，但不应阻断整个导入流程。
    warnings: tuple[str, ...] = ()

    @property
    def is_textual(self) -> bool:
        return bool(self.text.strip())


def _format_timestamp(seconds: float) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=0).isoformat()
