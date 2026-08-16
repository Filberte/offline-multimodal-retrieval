"""Week 6 集成检索服务测试，共 30 项。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from week4_retrieval.models import IndexingSummary, SearchFilters, SearchQuery
from week6_integration.service import IntegratedRetrievalService

from tests._support import make_record, make_service, write_text


class BatchCore:
    def __init__(self):
        self.calls = []
        self.engine = SimpleNamespace(
            text_backend=SimpleNamespace(space="batch-space", model_name="batch-model"),
            image_backend=None,
        )
        self.repository = SimpleNamespace(store=object(), scan=lambda **_: ())

    def index_paths(self, paths, *, continue_on_error=True):
        paths = tuple(paths)
        self.calls.append(paths)
        failures = tuple(
            {"path": str(path), "error": "bad", "error_type": "ValueError"}
            for path in paths
            if path.name.startswith("bad")
        )
        parsed = len(paths) - len(failures)
        return IndexingSummary(
            discovered_files=len(paths),
            parsed_files=parsed,
            parse_failures=failures,
            embedding_inputs=parsed,
            embedding_failures=(),
            persisted_vectors=parsed,
        )


class FailingCore:
    def __init__(self):
        self.engine = SimpleNamespace(
            text_backend=SimpleNamespace(space="text", model_name="failing"),
            image_backend=None,
        )
        self.repository = SimpleNamespace(store=object(), scan=lambda **_: ())

    def search(self, request):
        raise RuntimeError("planned failure")


class IntegratedServiceTests(unittest.TestCase):
    def test_181_constructor_rejects_zero_file_batch(self):
        core, _ = make_service()
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            IntegratedRetrievalService(core, file_batch_size=0)

    def test_182_constructor_keeps_core_reference(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        self.assertIs(service.core, core)

    def test_183_new_service_metrics_are_zero(self):
        core, _ = make_service()
        metrics = IntegratedRetrievalService(core).metrics
        self.assertEqual(
            (metrics.index_operations, metrics.search_operations),
            (0, 0),
        )

    def test_184_index_paths_records_operation(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        with tempfile.TemporaryDirectory() as temp:
            service.index_paths([write_text(Path(temp) / "a.txt", "alpha")])
        self.assertEqual(service.metrics.index_operations, 1)

    def test_185_index_paths_records_parsed_files(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        with tempfile.TemporaryDirectory() as temp:
            service.index_paths([write_text(Path(temp) / "a.txt", "alpha")])
        self.assertEqual(service.metrics.indexed_files, 1)

    def test_186_index_paths_records_persisted_vectors(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        with tempfile.TemporaryDirectory() as temp:
            service.index_paths([write_text(Path(temp) / "a.txt", "alpha")])
        self.assertEqual(service.metrics.persisted_vectors, 1)

    def test_187_index_paths_invalidates_query_cache(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        service.search(SearchQuery("alpha", include_cross_modal=False))
        service.search(SearchQuery("alpha", include_cross_modal=False))
        with tempfile.TemporaryDirectory() as temp:
            service.index_paths([write_text(Path(temp) / "a.txt", "alpha")])
        self.assertEqual(len(service.query_cache), 0)

    def test_188_first_search_records_operation(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        service.search(SearchQuery("alpha", include_cross_modal=False))
        self.assertEqual(service.metrics.search_operations, 1)

    def test_189_repeated_search_records_cache_hit(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        request = SearchQuery("alpha", include_cross_modal=False)
        service.search(request)
        service.search(request)
        self.assertEqual(service.metrics.search_cache_hits, 1)

    def test_190_query_cache_normalizes_case_and_whitespace(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        service.search(SearchQuery("Alpha", include_cross_modal=False))
        service.search(SearchQuery("  alpha  ", include_cross_modal=False))
        self.assertEqual(service.metrics.search_cache_hits, 1)

    def test_191_query_cache_distinguishes_top_k(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        service.search(SearchQuery("alpha", top_k=1, include_cross_modal=False))
        service.search(SearchQuery("alpha", top_k=2, include_cross_modal=False))
        self.assertEqual(service.metrics.search_cache_hits, 0)

    def test_192_query_cache_distinguishes_filters(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        service.search(SearchQuery("alpha", include_cross_modal=False))
        service.search(
            SearchQuery(
                "alpha",
                include_cross_modal=False,
                filters=SearchFilters(extension="txt"),
            )
        )
        self.assertEqual(service.metrics.search_cache_hits, 0)

    def test_193_invalid_query_is_rejected_without_operation(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        with self.assertRaises(ValueError):
            service.search(SearchQuery(" "))
        self.assertEqual(service.metrics.search_operations, 0)

    def test_194_backend_failure_increments_failure_metric(self):
        service = IntegratedRetrievalService(FailingCore())
        with self.assertRaisesRegex(RuntimeError, "planned"):
            service.search(SearchQuery("alpha", include_cross_modal=False))
        self.assertEqual(service.metrics.search_failures, 1)

    def test_195_search_latency_is_nonnegative(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        response = service.search(SearchQuery("alpha", include_cross_modal=False))
        self.assertGreaterEqual(response.elapsed_ms, 0)

    def test_196_empty_directory_returns_empty_summary(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        with tempfile.TemporaryDirectory() as temp:
            summary = service.index_directory(temp)
        self.assertEqual(summary.discovered_files, 0)

    def test_197_nonrecursive_directory_ignores_nested_file(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "nested").mkdir()
            write_text(root / "nested" / "a.txt", "alpha")
            summary = service.index_directory(root, recursive=False)
        self.assertEqual(summary.discovered_files, 0)

    def test_198_recursive_directory_finds_nested_file(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "nested").mkdir()
            write_text(root / "nested" / "a.txt", "alpha")
            summary = service.index_directory(root)
        self.assertEqual(summary.discovered_files, 1)

    def test_199_directory_uses_bounded_file_batches(self):
        core = BatchCore()
        service = IntegratedRetrievalService(core, file_batch_size=2)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(5):
                write_text(root / f"{index}.txt", f"text {index}")
            service.index_directory(root)
        self.assertEqual([len(batch) for batch in core.calls], [2, 2, 1])

    def test_200_directory_ignores_unsupported_extensions(self):
        core = BatchCore()
        service = IntegratedRetrievalService(core)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_text(root / "a.txt", "alpha")
            write_text(root / "a.csv", "alpha")
            summary = service.index_directory(root)
        self.assertEqual(summary.discovered_files, 1)

    def test_201_merge_summaries_combines_failures(self):
        first = IndexingSummary(1, 0, ({"path": "a", "error": "bad"},), 0, (), 0)
        second = IndexingSummary(
            1,
            1,
            (),
            1,
            ({"item_id": "b", "error": "bad"},),
            0,
        )
        merged = IntegratedRetrievalService._merge_summaries([first, second])
        self.assertEqual(
            (len(merged.parse_failures), len(merged.embedding_failures)),
            (1, 1),
        )

    def test_202_library_items_deduplicate_document_chunks(self):
        core, repository = make_service()
        space = core.engine.text_backend.space
        first = make_record("a:0", space=space, document_id="doc-a")
        second = make_record("a:1", space=space, document_id="doc-a")
        repository.records[(space, first.item_id)] = (first, (1.0,))
        repository.records[(space, second.item_id)] = (second, (1.0,))
        items = IntegratedRetrievalService(core).library_items()
        self.assertEqual(len(items), 1)

    def test_203_library_items_are_sorted_by_file_name(self):
        core, repository = make_service()
        space = core.engine.text_backend.space
        zulu = make_record("z", space=space, file_name="zulu.txt")
        alpha = make_record("a", space=space, file_name="alpha.txt")
        repository.records[(space, zulu.item_id)] = (zulu, (1.0,))
        repository.records[(space, alpha.item_id)] = (alpha, (1.0,))
        items = IntegratedRetrievalService(core).library_items()
        self.assertEqual(
            [item["file_name"] for item in items],
            ["alpha.txt", "zulu.txt"],
        )

    def test_204_library_item_preserves_source_path(self):
        core, repository = make_service()
        space = core.engine.text_backend.space
        record = make_record("a", space=space, source_path="C:/library/a.txt")
        repository.records[(space, record.item_id)] = (record, (1.0,))
        item = IntegratedRetrievalService(core).library_items()[0]
        self.assertEqual(item["source_path"], "C:/library/a.txt")

    def test_205_library_item_invalid_chunk_index_becomes_none(self):
        core, repository = make_service()
        space = core.engine.text_backend.space
        record = make_record("a", space=space, chunk_index="invalid")
        repository.records[(space, record.item_id)] = (record, (1.0,))
        item = IntegratedRetrievalService(core).library_items()[0]
        self.assertIsNone(item["chunk_index"])

    def test_206_health_is_ready_without_issues(self):
        core, _ = make_service()
        health = IntegratedRetrievalService(core).health()
        self.assertTrue(health.ready)

    def test_207_health_is_degraded_with_issue(self):
        core, _ = make_service()
        health = IntegratedRetrievalService(core).health(issues=["disk warning"])
        self.assertEqual(health.status, "degraded")

    def test_208_health_confirms_offline_only(self):
        core, _ = make_service()
        health = IntegratedRetrievalService(core).health()
        self.assertTrue(health.offline_only)

    def test_209_health_exposes_vector_store_type(self):
        core, _ = make_service()
        health = IntegratedRetrievalService(core).health()
        self.assertEqual(health.vector_store, "MemoryRepository")

    def test_210_health_metrics_reflect_completed_search(self):
        core, _ = make_service()
        service = IntegratedRetrievalService(core)
        service.search(SearchQuery("alpha", include_cross_modal=False))
        self.assertEqual(service.health().metrics.search_operations, 1)


if __name__ == "__main__":
    unittest.main()
