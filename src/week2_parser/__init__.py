"""Week 2 文件解析模块的公共 API。"""

from week2_parser.ingestion import BatchIngestionResult, ingest_files
from week2_parser.models import FileMetadata, ParseResult
from week2_parser.parsers import FileParser, parse_file

__all__ = [
    "BatchIngestionResult",
    "FileMetadata",
    "FileParser",
    "ParseResult",
    "ingest_files",
    "parse_file",
]
