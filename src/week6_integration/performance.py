"""可重复的延迟、并发与内存基准工具。"""

from __future__ import annotations

import tracemalloc
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from statistics import mean, median
from time import perf_counter
from typing import Callable, Generic, Iterable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class LatencyStats:
    iterations: int
    minimum_ms: float
    median_ms: float
    mean_ms: float
    p95_ms: float
    maximum_ms: float
    throughput_per_second: float

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


@dataclass(frozen=True)
class StressResult:
    operations: int
    concurrency: int
    succeeded: int
    failed: int
    elapsed_seconds: float
    p95_ms: float

    @property
    def success_rate(self) -> float:
        return self.succeeded / self.operations if self.operations else 1.0

    def to_dict(self) -> dict[str, int | float]:
        payload = asdict(self)
        payload["success_rate"] = round(self.success_rate, 6)
        return payload


@dataclass(frozen=True)
class MemoryResult(Generic[T]):
    value: T
    current_bytes: int
    peak_bytes: int


def percentile(values: Iterable[float], percent: float) -> float:
    """按线性插值计算百分位。"""

    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("percentile requires at least one value")
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    position = (len(ordered) - 1) * percent / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def measure_operation(
    operation: Callable[[], object],
    *,
    iterations: int,
    warmups: int = 1,
) -> LatencyStats:
    """执行预热和多轮测量，返回延迟分布与吞吐。"""

    if iterations <= 0:
        raise ValueError("iterations must be greater than zero")
    if warmups < 0:
        raise ValueError("warmups must not be negative")
    for _ in range(warmups):
        operation()
    samples: list[float] = []
    started = perf_counter()
    for _ in range(iterations):
        item_started = perf_counter()
        operation()
        samples.append((perf_counter() - item_started) * 1000)
    elapsed = perf_counter() - started
    return LatencyStats(
        iterations=iterations,
        minimum_ms=round(min(samples), 6),
        median_ms=round(median(samples), 6),
        mean_ms=round(mean(samples), 6),
        p95_ms=round(percentile(samples, 95), 6),
        maximum_ms=round(max(samples), 6),
        throughput_per_second=round(iterations / elapsed if elapsed else 0.0, 3),
    )


def improvement_percent(baseline: float, optimized: float) -> float:
    """计算越低越优指标的百分比改善。"""

    if baseline <= 0:
        raise ValueError("baseline must be greater than zero")
    return (baseline - optimized) / baseline * 100


def profile_memory(operation: Callable[[], T]) -> MemoryResult[T]:
    """使用标准库 tracemalloc 记录当前与峰值 Python 内存。"""

    tracemalloc.start()
    try:
        value = operation()
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return MemoryResult(value=value, current_bytes=current, peak_bytes=peak)


def run_stress(
    operation: Callable[[int], object],
    *,
    operations: int,
    concurrency: int,
) -> StressResult:
    """并发执行固定次数操作并汇总错误率与 P95 延迟。"""

    if operations < 0:
        raise ValueError("operations must not be negative")
    if concurrency <= 0:
        raise ValueError("concurrency must be greater than zero")
    if operations == 0:
        return StressResult(0, concurrency, 0, 0, 0.0, 0.0)
    samples: list[float] = []
    failures = 0
    started = perf_counter()

    def measured(index: int) -> float:
        item_started = perf_counter()
        operation(index)
        return (perf_counter() - item_started) * 1000

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(measured, index) for index in range(operations)]
        for future in as_completed(futures):
            try:
                samples.append(future.result())
            except Exception:
                failures += 1
    elapsed = perf_counter() - started
    return StressResult(
        operations=operations,
        concurrency=concurrency,
        succeeded=operations - failures,
        failed=failures,
        elapsed_seconds=round(elapsed, 6),
        p95_ms=round(percentile(samples, 95), 6) if samples else 0.0,
    )
