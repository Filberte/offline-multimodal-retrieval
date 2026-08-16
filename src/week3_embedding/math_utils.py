"""不依赖大型计算框架的基础向量工具。"""

from __future__ import annotations

import math
from typing import Iterable, Sequence


def l2_normalize(values: Iterable[float]) -> tuple[float, ...]:
    # 统一转为不可变浮点元组，避免调用方后续修改原始数组。
    vector = tuple(float(value) for value in values)
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        raise ValueError("cannot normalize a zero vector")
    return tuple(value / norm for value in vector)


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    # 先校验维度再归一化，禁止不同嵌入空间误算相似度。
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimension")
    if not left:
        raise ValueError("vectors must not be empty")
    left_n = l2_normalize(left)
    right_n = l2_normalize(right)
    return sum(a * b for a, b in zip(left_n, right_n))
