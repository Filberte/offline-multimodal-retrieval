"""Week2-Week4 索引与检索服务测试，共 18 项。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from week3_embedding.backends import HashingTextBackend
from week3_embedding.engine import EmbeddingEngine
from week4_retrieval.models import SearchFilters, SearchQuery
from week4_retrieval.service import CoreRetrievalService

from tests._support import MemoryRepository, make_service, write_text


class ServiceTests(unittest.TestCase):
    def test_075_constructor_rejects_nonpositive_batch_size(self):
        with self.assertRaisesRegex(ValueError, "must be positive"):
            CoreRetrievalService(
                engine=EmbeddingEngine(text_backend=HashingTextBackend()),
                repository=MemoryRepository(),
                batch_size=0,
            )

    def test_076_constructor_rejects_nonpositive_candidate_multiplier(self):
        with self.assertRaisesRegex(ValueError, "must be positive"):
            CoreRetrievalService(
                engine=EmbeddingEngine(text_backend=HashingTextBackend()),
                repository=MemoryRepository(),
                candidate_multiplier=0,
            )

    def test_077_index_paths_processes_single_text_file(self):
        service, _ = make_service()
        with tempfile.TemporaryDirectory() as temp:
            path = write_text(Path(temp) / "a.txt", "offline local retrieval")
            summary = service.index_paths([path])
        self.assertEqual(
            (summary.discovered_files, summary.parsed_files, summary.persisted_vectors),
            (1, 1, 1),
        )

    def test_078_index_paths_processes_multiple_text_files(self):
        service, _ = make_service(batch_size=1)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = [
                write_text(root / "a.txt", "offline retrieval"),
                write_text(root / "b.txt", "vector database"),
                write_text(root / "c.txt", "privacy search"),
            ]
            summary = service.index_paths(paths)
        self.assertEqual(summary.persisted_vectors, 3)

    def test_079_index_directory_discovers_nested_files_recursively(self):
        service, _ = make_service()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_text(root / "a.txt", "root document")
            nested = root / "nested"
            nested.mkdir()
            write_text(nested / "b.txt", "nested document")
            summary = service.index_directory(root)
        self.assertEqual(summary.discovered_files, 2)

    def test_080_index_directory_can_disable_recursion(self):
        service, _ = make_service()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_text(root / "a.txt", "root document")
            nested = root / "nested"
            nested.mkdir()
            write_text(nested / "b.txt", "nested document")
            summary = service.index_directory(root, recursive=False)
        self.assertEqual(summary.discovered_files, 1)

    def test_081_missing_file_is_recorded_when_continuing(self):
        service, _ = make_service()
        missing = Path(tempfile.gettempdir()) / "week4_missing_081.txt"
        summary = service.index_paths([missing])
        self.assertEqual(len(summary.parse_failures), 1)

    def test_082_missing_file_raises_in_strict_mode(self):
        service, _ = make_service()
        missing = Path(tempfile.gettempdir()) / "week4_missing_082.txt"
        with self.assertRaises(OSError):
            service.index_paths([missing], continue_on_error=False)

    def test_083_search_returns_relevant_file_first(self):
        service, _ = make_service()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            service.index_paths(
                [
                    write_text(root / "privacy.txt", "offline private documents"),
                    write_text(root / "cloud.txt", "network synchronization"),
                ]
            )
            response = service.search(
                SearchQuery("offline private", top_k=2, include_cross_modal=False)
            )
        self.assertEqual(response.hits[0].file_name, "privacy.txt")

    def test_084_search_reports_nonnegative_elapsed_time(self):
        service, _ = make_service()
        with tempfile.TemporaryDirectory() as temp:
            service.index_paths([write_text(Path(temp) / "a.txt", "local search")])
            response = service.search(
                SearchQuery("local", include_cross_modal=False)
            )
        self.assertGreaterEqual(response.elapsed_ms, 0)

    def test_085_search_warns_when_cross_modal_backend_is_absent(self):
        service, _ = make_service()
        response = service.search(SearchQuery("local", top_k=1))
        self.assertEqual(len(response.warnings), 1)

    def test_086_search_has_no_warning_with_cross_modal_backend(self):
        service, _ = make_service(cross_modal=True)
        response = service.search(SearchQuery("local", top_k=1))
        self.assertEqual(response.warnings, ())

    def test_087_candidate_limit_has_minimum_of_twenty(self):
        service, repository = make_service(candidate_multiplier=2)
        service.search(
            SearchQuery("local", top_k=3, include_cross_modal=False)
        )
        self.assertEqual(repository.semantic_calls[0]["n_results"], 20)

    def test_088_candidate_limit_scales_with_top_k(self):
        service, repository = make_service(candidate_multiplier=5)
        service.search(
            SearchQuery("local", top_k=10, include_cross_modal=False)
        )
        self.assertEqual(repository.semantic_calls[0]["n_results"], 50)

    def test_089_extension_filter_is_passed_to_repository(self):
        service, repository = make_service()
        service.search(
            SearchQuery(
                "local",
                include_cross_modal=False,
                filters=SearchFilters(extension="txt"),
            )
        )
        self.assertEqual(
            repository.semantic_calls[0]["where"],
            {"extension": {"$eq": "txt"}},
        )

    def test_090_source_path_filter_is_applied_after_recall(self):
        service, _ = make_service()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            service.index_paths(
                [
                    write_text(root / "keep.txt", "local retrieval"),
                    write_text(root / "drop.txt", "local retrieval"),
                ]
            )
            response = service.search(
                SearchQuery(
                    "local",
                    include_cross_modal=False,
                    filters=SearchFilters(source_path_contains="keep.txt"),
                )
            )
        self.assertTrue(all("keep.txt" in hit.source_path for hit in response.hits))

    def test_091_invalid_query_is_rejected_before_embedding(self):
        service, repository = make_service()
        with self.assertRaises(ValueError):
            service.search(SearchQuery(" "))
        self.assertEqual(repository.semantic_calls, [])

    def test_092_candidate_count_deduplicates_semantic_and_keyword_match(self):
        service, _ = make_service()
        with tempfile.TemporaryDirectory() as temp:
            service.index_paths([write_text(Path(temp) / "a.txt", "local local")])
            response = service.search(
                SearchQuery("local", include_cross_modal=False)
            )
        self.assertEqual(response.candidate_count, 1)


if __name__ == "__main__":
    unittest.main()
