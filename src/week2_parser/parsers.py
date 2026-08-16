"""TXT、PDF、DOCX、JPG、PNG 的核心解析器实现。"""

from __future__ import annotations

import re
import struct
import zipfile
from abc import ABC, abstractmethod
from html import unescape
from pathlib import Path
from typing import Callable

from week2_parser.models import FileMetadata, ParseResult


class UnsupportedFileTypeError(ValueError):
    """没有任何解析器支持当前文件扩展名时抛出。"""


class FileParser(ABC):
    """所有具体文件解析器的基类。"""

    content_type = "application/octet-stream"

    @abstractmethod
    def parse(self, path: Path) -> ParseResult:
        """解析单个文件并返回标准化文本与元数据。"""


# TXT 是最基础的文本输入格式，后续会直接进入文本切分和 BERT 嵌入流程。
class TextParser(FileParser):
    content_type = "text/plain"

    def parse(self, path: Path) -> ParseResult:
        warnings: list[str] = []
        # 优先按 UTF-8 读取；如果遇到非法字节，不让整个导入任务失败，而是记录 warning。
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
            warnings.append("TXT 文件包含非法 UTF-8 字节，已使用替换字符继续解析。")

        # 行数和字符数属于轻量元数据，后续 UI 可以用来显示文件预览和导入质量。
        metadata = FileMetadata.from_path(
            path,
            content_type=self.content_type,
            extra={"line_count": _count_lines(text), "character_count": len(text)},
        )
        return ParseResult(metadata=metadata, text=text, warnings=tuple(warnings))


# DOCX 本质是一个 OpenXML 压缩包，这里直接读取 word/document.xml 提取段落文本。
# 这样做不依赖 Word 软件，符合离线优先的项目方向。
class DocxParser(FileParser):
    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def parse(self, path: Path) -> ParseResult:
        warnings: list[str] = []
        with zipfile.ZipFile(path) as archive:
            document_xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
            core_props = _read_docx_core_properties(archive)

        # 先按段落抽取，再拼成纯文本；后续 embedding 层可以在此基础上做 chunking。
        paragraphs = re.findall(r"<w:p\b[^>]*>(.*?)</w:p>", document_xml, flags=re.DOTALL)
        text_blocks = [_extract_docx_paragraph_text(paragraph) for paragraph in paragraphs]
        text = "\n".join(block for block in text_blocks if block.strip())
        if not text:
            warnings.append("DOCX 文件没有可提取的段落文本。")

        metadata = FileMetadata.from_path(
            path,
            content_type=self.content_type,
            extra={
                "paragraph_count": len([block for block in text_blocks if block.strip()]),
                **core_props,
            },
        )
        return ParseResult(metadata=metadata, text=text, warnings=tuple(warnings))


# PDF 是本项目最核心的本地文档格式之一。Week 2 先完成文本型 PDF 的基础抽取；
# 扫描版 PDF/OCR 属于后续多模态增强范围。
class PdfParser(FileParser):
    content_type = "application/pdf"

    def parse(self, path: Path) -> ParseResult:
        warnings: list[str] = []
        text = ""
        page_count = 0

        try:
            from pypdf import PdfReader

            # page_count 会进入元数据，后续 UI 可展示页数，检索结果也能回溯来源。
            reader = PdfReader(str(path))
            page_count = len(reader.pages)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:  # pragma: no cover - 仅在 pypdf 不可用或文件损坏时触发。
            warnings.append(f"pypdf 文本提取失败：{exc}")
            raw = path.read_bytes()
            text = _fallback_pdf_text(raw)
            page_count = raw.count(b"/Type /Page")

        if not text.strip():
            warnings.append("PDF 文件没有可提取文本。")

        metadata = FileMetadata.from_path(
            path,
            content_type=self.content_type,
            extra={"page_count": page_count},
        )
        return ParseResult(metadata=metadata, text=text, warnings=tuple(warnings))


# 图片在 Week 2 阶段先提取尺寸和类型，Week 3 再接入 MobileCLIP 图片嵌入。
class PngParser(FileParser):
    content_type = "image/png"

    def parse(self, path: Path) -> ParseResult:
        with path.open("rb") as handle:
            # 通过文件签名判断真 PNG，避免只靠扩展名导致误解析。
            signature = handle.read(8)
            if signature != b"\x89PNG\r\n\x1a\n":
                raise ValueError("PNG 文件签名无效。")
            chunk_length = struct.unpack(">I", handle.read(4))[0]
            chunk_type = handle.read(4)
            if chunk_type != b"IHDR" or chunk_length < 13:
                raise ValueError("PNG 文件缺少有效 IHDR 头。")
            width, height = struct.unpack(">II", handle.read(8))

        metadata = FileMetadata.from_path(
            path,
            content_type=self.content_type,
            extra={"width": width, "height": height},
        )
        return ParseResult(metadata=metadata, text=_image_summary("PNG", width, height))


# JPG/JPEG 解析逻辑与 PNG 分开实现，因为两种图片格式的二进制头结构不同。
class JpegParser(FileParser):
    content_type = "image/jpeg"

    def parse(self, path: Path) -> ParseResult:
        width, height = _read_jpeg_dimensions(path)
        metadata = FileMetadata.from_path(
            path,
            content_type=self.content_type,
            extra={"width": width, "height": height},
        )
        return ParseResult(metadata=metadata, text=_image_summary("JPEG", width, height))


# 解析器注册表：批量导入层只看扩展名，不需要知道每种格式的内部细节。
# 后续如果要增加 CSV、MD、HTML 等格式，只需要新增 parser 并在这里注册。
PARSER_FACTORIES: dict[str, Callable[[], FileParser]] = {
    "txt": TextParser,
    "pdf": PdfParser,
    "docx": DocxParser,
    "png": PngParser,
    "jpg": JpegParser,
    "jpeg": JpegParser,
}


def parse_file(path: str | Path) -> ParseResult:
    """根据扩展名选择解析器并解析受支持文件。"""

    resolved = Path(path)
    extension = resolved.suffix.lower().lstrip(".")
    # 这里故意对不支持格式抛出明确异常，方便批量导入层记录 failed。
    try:
        parser = PARSER_FACTORIES[extension]()
    except KeyError as exc:
        raise UnsupportedFileTypeError(f"不支持的文件类型：{extension or '<无扩展名>'}") from exc
    return parser.parse(resolved)


def _count_lines(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def _extract_docx_paragraph_text(paragraph_xml: str) -> str:
    fragments = re.findall(r"<w:t\b[^>]*>(.*?)</w:t>", paragraph_xml, flags=re.DOTALL)
    return "".join(unescape(_strip_xml_tags(fragment)) for fragment in fragments)


def _read_docx_core_properties(archive: zipfile.ZipFile) -> dict[str, str]:
    try:
        xml = archive.read("docProps/core.xml").decode("utf-8", errors="replace")
    except KeyError:
        return {}

    props: dict[str, str] = {}
    for field in ("title", "creator", "description"):
        match = re.search(fr"<dc:{field}[^>]*>(.*?)</dc:{field}>", xml, flags=re.DOTALL)
        if match:
            props[field] = unescape(_strip_xml_tags(match.group(1))).strip()
    return props


def _strip_xml_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)


def _fallback_pdf_text(raw: bytes) -> str:
    matches = re.findall(rb"\(([^()]*)\)\s*Tj", raw)
    return "\n".join(match.decode("latin-1", errors="replace") for match in matches)


def _image_summary(kind: str, width: int, height: int) -> str:
    return f"{kind} 图片：{width}x{height} 像素"


# JPEG 没有像 PNG 那样固定位置的宽高字段，所以需要扫描 SOF 标记。
def _read_jpeg_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        if handle.read(2) != b"\xff\xd8":
            raise ValueError("JPEG 文件签名无效。")
        while True:
            marker_start = handle.read(1)
            if marker_start == b"":
                break
            if marker_start != b"\xff":
                continue
            marker = handle.read(1)
            while marker == b"\xff":
                marker = handle.read(1)
            if marker in {b"\xc0", b"\xc1", b"\xc2", b"\xc3", b"\xc5", b"\xc6", b"\xc7", b"\xc9", b"\xca", b"\xcb", b"\xcd", b"\xce", b"\xcf"}:
                segment_length = struct.unpack(">H", handle.read(2))[0]
                if segment_length < 7:
                    raise ValueError("JPEG SOF 段无效。")
                handle.read(1)
                height, width = struct.unpack(">HH", handle.read(4))
                return width, height
            if marker in {b"\xd8", b"\xd9"}:
                continue
            length_bytes = handle.read(2)
            if len(length_bytes) != 2:
                break
            segment_length = struct.unpack(">H", length_bytes)[0]
            handle.seek(segment_length - 2, 1)
    raise ValueError("未找到 JPEG 图片尺寸。")
