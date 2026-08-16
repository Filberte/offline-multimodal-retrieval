"""Week 6 LRU 与嵌入缓存测试，共 30 项。"""

from __future__ import annotations

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from week3_embedding.backends import HashingTextBackend
from week3_embedding.engine import EmbeddingEngine
from week3_embedding.models import EmbeddingInput, Modality
from week6_integration.cache import LruCache
from week6_integration.embedding import CachedEmbeddingEngine


class CountingBackend(HashingTextBackend):
    def __init__(self, dimension=32):
        super().__init__(dimension=dimension)
        self.calls = 0
        self.batch_sizes = []

    def embed_texts(self, texts):
        self.calls += 1
        self.batch_sizes.append(len(texts))
        return super().embed_texts(texts)


class CrossCountingBackend(CountingBackend):
    model_name = "cross-counting"
    space = "mobileclip-test-v1"


def text_item(item_id: str, text: str, **metadata) -> EmbeddingInput:
    return EmbeddingInput(
        item_id=item_id,
        modality=Modality.TEXT,
        text=text,
        metadata=metadata,
    )


def make_cached(*, capacity=8, cross=False):
    backend = CountingBackend()
    cross_backend = CrossCountingBackend() if cross else None
    engine = CachedEmbeddingEngine(
        EmbeddingEngine(
            text_backend=backend,
            cross_modal_text_backend=cross_backend,
        ),
        cache_size=capacity,
    )
    return engine, backend, cross_backend


class CacheEmbeddingTests(unittest.TestCase):
    def test_151_lru_rejects_zero_capacity(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            LruCache(0)

    def test_152_lru_rejects_negative_capacity(self):
        with self.assertRaises(ValueError):
            LruCache(-2)

    def test_153_new_lru_is_empty(self):
        cache = LruCache(2)
        self.assertEqual(len(cache), 0)

    def test_154_missing_lru_key_increments_miss(self):
        cache = LruCache(2)
        self.assertIsNone(cache.get("missing"))
        self.assertEqual(cache.stats.misses, 1)

    def test_155_lru_put_then_get_increments_hit(self):
        cache = LruCache(2)
        cache.put("a", 1)
        self.assertEqual(cache.get("a"), 1)
        self.assertEqual(cache.stats.hits, 1)

    def test_156_lru_overwrite_does_not_grow(self):
        cache = LruCache(2)
        cache.put("a", 1)
        cache.put("a", 2)
        self.assertEqual((len(cache), cache.get("a")), (1, 2))

    def test_157_lru_evicts_oldest_entry(self):
        cache = LruCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        self.assertNotIn("a", cache)
        self.assertEqual(cache.stats.evictions, 1)

    def test_158_lru_get_refreshes_recency(self):
        cache = LruCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")
        cache.put("c", 3)
        self.assertIn("a", cache)
        self.assertNotIn("b", cache)

    def test_159_lru_clear_removes_entries(self):
        cache = LruCache(2)
        cache.put("a", 1)
        cache.clear()
        self.assertEqual(len(cache), 0)

    def test_160_lru_clear_can_reset_statistics(self):
        cache = LruCache(2)
        cache.get("a")
        cache.put("a", 1)
        cache.get("a")
        cache.clear(reset_statistics=True)
        self.assertEqual((cache.stats.hits, cache.stats.misses), (0, 0))

    def test_161_lru_clear_preserves_statistics_by_default(self):
        cache = LruCache(2)
        cache.get("a")
        cache.clear()
        self.assertEqual(cache.stats.misses, 1)

    def test_162_lru_contains_reports_existing_key(self):
        cache = LruCache(2)
        cache.put("a", 1)
        self.assertTrue("a" in cache)

    def test_163_cache_stats_requests_sum_hits_and_misses(self):
        cache = LruCache(2)
        cache.get("a")
        cache.put("a", 1)
        cache.get("a")
        self.assertEqual(cache.stats.requests, 2)

    def test_164_cache_stats_hit_rate_is_bounded(self):
        cache = LruCache(2)
        cache.put("a", 1)
        cache.get("a")
        cache.get("b")
        self.assertEqual(cache.stats.hit_rate, 0.5)

    def test_165_lru_remains_bounded_under_parallel_writes(self):
        cache = LruCache(16)
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(lambda value: cache.put(value, value), range(200)))
        self.assertLessEqual(len(cache), 16)

    def test_166_cached_engine_uses_requested_capacity(self):
        engine, _, _ = make_cached(capacity=3)
        self.assertEqual(engine.cache.stats.capacity, 3)

    def test_167_first_embed_invokes_backend(self):
        engine, backend, _ = make_cached()
        engine.embed(text_item("a", "local semantic retrieval"))
        self.assertEqual(backend.calls, 1)

    def test_168_second_identical_embed_hits_cache(self):
        engine, backend, _ = make_cached()
        item = text_item("a", "local semantic retrieval")
        engine.embed(item)
        engine.embed(item)
        self.assertEqual((backend.calls, engine.cache.stats.hits), (1, 1))

    def test_169_same_content_with_new_id_reuses_vector(self):
        engine, backend, _ = make_cached()
        first = engine.embed(text_item("a", "shared content"))
        second = engine.embed(text_item("b", "shared content"))
        self.assertEqual(first.values, second.values)
        self.assertEqual((second.item_id, backend.calls), ("b", 1))

    def test_170_embedding_spaces_have_independent_cache_keys(self):
        engine, backend, cross = make_cached(cross=True)
        item = text_item("a", "cross modal query")
        engine.embed(item, space="default")
        engine.embed(item, space="cross_modal")
        self.assertEqual((backend.calls, cross.calls), (1, 1))

    def test_171_cached_vector_restores_current_metadata(self):
        engine, _, _ = make_cached()
        engine.embed(text_item("a", "same text", source="one"))
        result = engine.embed(text_item("b", "same text", source="two"))
        self.assertEqual(result.metadata["source"], "two")

    def test_172_batch_misses_use_one_backend_call(self):
        engine, backend, _ = make_cached()
        result = engine.embed_batch(
            [text_item("a", "alpha"), text_item("b", "beta")]
        )
        self.assertEqual((len(result.vectors), backend.calls), (2, 1))
        self.assertEqual(backend.batch_sizes, [2])

    def test_173_batch_deduplicates_equal_content(self):
        engine, backend, _ = make_cached()
        result = engine.embed_batch(
            [text_item("a", "same"), text_item("b", "same")]
        )
        self.assertEqual(len(result.vectors), 2)
        self.assertEqual(backend.batch_sizes, [1])

    def test_174_batch_preserves_input_order(self):
        engine, _, _ = make_cached()
        result = engine.embed_batch(
            [text_item("z", "zulu"), text_item("a", "alpha")]
        )
        self.assertEqual([item.item_id for item in result.vectors], ["z", "a"])

    def test_175_batch_combines_cached_and_new_items(self):
        engine, backend, _ = make_cached()
        engine.embed(text_item("a", "alpha"))
        result = engine.embed_batch(
            [text_item("a2", "alpha"), text_item("b", "beta")]
        )
        self.assertEqual([item.item_id for item in result.vectors], ["a2", "b"])
        self.assertEqual(backend.calls, 2)

    def test_176_batch_records_invalid_text_item(self):
        engine, _, _ = make_cached()
        result = engine.embed_batch(
            [EmbeddingInput("", Modality.TEXT, text="valid text")]
        )
        self.assertEqual(result.failures[0].error_type, "ValueError")

    def test_177_batch_strict_mode_raises_invalid_item(self):
        engine, _, _ = make_cached()
        with self.assertRaises(ValueError):
            engine.embed_batch(
                [EmbeddingInput("", Modality.TEXT, text="valid text")],
                continue_on_error=False,
            )

    def test_178_batch_records_missing_image(self):
        engine, _, _ = make_cached()
        missing = Path(tempfile.gettempdir()) / "week6_missing_image_178.png"
        result = engine.embed_batch(
            [EmbeddingInput("image", Modality.IMAGE, image_path=str(missing))]
        )
        self.assertEqual(result.failures[0].error_type, "FileNotFoundError")

    def test_179_embedding_cache_evicts_when_full(self):
        engine, backend, _ = make_cached(capacity=1)
        engine.embed(text_item("a", "alpha"))
        engine.embed(text_item("b", "beta"))
        engine.embed(text_item("c", "alpha"))
        self.assertEqual((backend.calls, engine.cache.stats.evictions), (3, 2))

    def test_180_cache_stats_serializes_rate_and_requests(self):
        cache = LruCache(2)
        cache.put("a", 1)
        cache.get("a")
        payload = cache.stats.to_dict()
        self.assertEqual((payload["requests"], payload["hit_rate"]), (1, 1.0))


if __name__ == "__main__":
    unittest.main()
