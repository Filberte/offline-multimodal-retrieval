"""批量文件导入和元数据提取。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from week2_parser.models import ParseResult
from week2_parser.parsers import UnsupportedFileTypeError, parse_file


@dataclass(frozen=True)
class BatchIngestionResult:
    """批量导入任务的结构化结果。"""

    # parsed 保存成功解析结果；failed 保存失败文件及原因。
    # 这样批量导入一个文件夹时，不会因为一个坏文件丢掉全部成果。
    parsed: tuple[ParseResult, ...] = ()
    failed: tuple[dict[str, str], ...] = ()

    @property
    def total_files(self) -> int:
        return len(self.parsed) + len(self.failed)

    @property
    def success_rate(self) -> float:
        if self.total_files == 0:
            return 1.0
        return len(self.parsed) / self.total_files


def ingest_files(paths: Iterable[str | Path], *, continue_on_error: bool = True) -> BatchIngestionResult:
    """批量解析文件；默认保留成功结果并记录单文件失败原因。"""

    parsed: list[ParseResult] = []
    failed: list[dict[str, str]] = []

    # 逐个文件处理，保证错误隔离；这是后续大规模本地文件库导入的基础能力。
    for raw_path in paths:
        path = Path(raw_path)
        try:
            parsed.append(parse_file(path))
        except (OSError, ValueError, UnsupportedFileTypeError) as exc:
            # 严格模式用于开发和测试；默认模式用于真实批量导入，尽量不中断任务。
            if not continue_on_error:
                raise
            failed.append({"path": str(path), "error": str(exc), "error_type": type(exc).__name__})

    return BatchIngestionResult(parsed=tuple(parsed), failed=tuple(failed))


def discover_files(root: str | Path, *, recursive: bool = True) -> tuple[Path, ...]:
    """扫描目录，返回当前解析模块支持的文件。"""

    base = Path(root)
    pattern = "**/*" if recursive else "*"
    # Week 2 要求明确限定为 TXT/PDF/DOCX/JPG/PNG；CSV 不在本周要求内。
    supported = {".txt", ".pdf", ".docx", ".jpg", ".jpeg", ".png"}
    return tuple(path for path in base.glob(pattern) if path.is_file() and path.suffix.lower() in supported)
