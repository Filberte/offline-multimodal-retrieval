"""Week3 嵌入层对外公开的数据契约。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Sequence


class Modality(str, Enum):
    # 使用字符串枚举便于 JSON 序列化及跨模块传输。
    TEXT = "text"
    IMAGE = "image"


@dataclass(frozen=True)
class EmbeddingInput:
    """统一嵌入引擎接收的标准化输入。"""

    item_id: str
    modality: Modality
    text: str | None = None
    image_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        # 文本和图像采用互斥校验规则，并在推理前确认图像文件存在。
        if not self.item_id.strip():
            raise ValueError("item_id must not be empty")
        if self.modality is Modality.TEXT and not (self.text or "").strip():
            raise ValueError("text input must contain non-whitespace text")
        if self.modality is Modality.IMAGE:
            if not self.image_path:
                raise ValueError("image input must provide image_path")
            path = Path(self.image_path)
            if not path.is_file():
                raise FileNotFoundError(path)


@dataclass(frozen=True)
class EmbeddingVector:
    """单条归一化向量及 Week4 入库所需的来源信息。"""

    item_id: str
    modality: Modality
    space: str
    model_name: str
    values: tuple[float, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def dimension(self) -> int:
        return len(self.values)


@dataclass(frozen=True)
class BatchFailure:
    # 保留失败条目的标识、异常类型和信息，支持后续重试。
    item_id: str
    error_type: str
    error: str


@dataclass(frozen=True)
class BatchEmbeddingResult:
    # 批处理结果同时返回成功向量与失败记录，避免静默丢失数据。
    vectors: tuple[EmbeddingVector, ...] = ()
    failures: tuple[BatchFailure, ...] = ()

    @property
    def total_items(self) -> int:
        return len(self.vectors) + len(self.failures)

    @property
    def success_rate(self) -> float:
        return 1.0 if not self.total_items else len(self.vectors) / self.total_items


def as_float_tuple(values: Sequence[float]) -> tuple[float, ...]:
    # 在数据契约边界统一数值类型和不可变性。
    return tuple(float(value) for value in values)
