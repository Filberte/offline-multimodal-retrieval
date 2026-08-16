"""线程安全的有界 LRU 缓存。"""

from __future__ import annotations

from collections import OrderedDict
from threading import RLock
from typing import Generic, TypeVar

from week6_integration.models import CacheStats

K = TypeVar("K")
V = TypeVar("V")
_MISSING = object()


class LruCache(Generic[K, V]):
    """按最近使用顺序淘汰条目，并记录可观测指标。"""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("cache capacity must be greater than zero")
        self.capacity = capacity
        self._values: OrderedDict[K, V] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._lock = RLock()

    def get(self, key: K, default: V | None = None) -> V | None:
        """读取并提升条目优先级；缺失时返回调用方默认值。"""

        with self._lock:
            value = self._values.get(key, _MISSING)
            if value is _MISSING:
                self._misses += 1
                return default
            self._values.move_to_end(key)
            self._hits += 1
            return value  # type: ignore[return-value]

    def put(self, key: K, value: V) -> None:
        """新增或更新条目，并在超出容量时淘汰最旧条目。"""

        with self._lock:
            if key in self._values:
                self._values.move_to_end(key)
            self._values[key] = value
            while len(self._values) > self.capacity:
                self._values.popitem(last=False)
                self._evictions += 1

    def clear(self, *, reset_statistics: bool = False) -> None:
        """清空缓存；可选地同时清零累计统计。"""

        with self._lock:
            self._values.clear()
            if reset_statistics:
                self._hits = self._misses = self._evictions = 0

    def __contains__(self, key: object) -> bool:
        with self._lock:
            return key in self._values

    def __len__(self) -> int:
        with self._lock:
            return len(self._values)

    @property
    def stats(self) -> CacheStats:
        with self._lock:
            return CacheStats(
                hits=self._hits,
                misses=self._misses,
                evictions=self._evictions,
                size=len(self._values),
                capacity=self.capacity,
            )
