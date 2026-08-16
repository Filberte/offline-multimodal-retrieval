"""数据契约、过滤条件与序列化测试，共 24 项。"""

from __future__ import annotations

import unittest

from week4_retrieval.models import (
    IndexingSummary,
    RetrievalHit,
    SearchFilters,
    SearchQuery,
    SearchResponse,
    StoredRecord,
)


class ModelsTests(unittest.TestCase):
    def test_001_empty_filters_have_no_chroma_where(self):
        self.assertIsNone(SearchFilters().to_chroma_where())

    def test_002_single_modality_filter_builds_single_clause(self):
        self.assertEqual(
            SearchFilters(modality="text").to_chroma_where(),
            {"modality": {"$eq": "text"}},
        )

    def test_003_single_content_type_filter_builds_single_clause(self):
        self.assertEqual(
            SearchFilters(content_type="text/plain").to_chroma_where(),
            {"content_type": {"$eq": "text/plain"}},
        )

    def test_004_multiple_exact_filters_build_and_clause(self):
        where = SearchFilters(
            modality="text",
            extension="pdf",
            document_id="doc-1",
        ).to_chroma_where()
        self.assertEqual(len(where["$and"]), 3)

    def test_005_path_contains_is_post_filter_only(self):
        where = SearchFilters(source_path_contains="Reports").to_chroma_where()
        self.assertIsNone(where)

    def test_006_empty_filters_accept_any_metadata(self):
        self.assertTrue(SearchFilters().accepts({}))

    def test_007_exact_filters_accept_matching_metadata(self):
        filters = SearchFilters(modality="text", extension="txt")
        self.assertTrue(filters.accepts({"modality": "text", "extension": "txt"}))

    def test_008_exact_filters_reject_wrong_modality(self):
        filters = SearchFilters(modality="text")
        self.assertFalse(filters.accepts({"modality": "image"}))

    def test_009_exact_filters_reject_missing_content_type(self):
        filters = SearchFilters(content_type="text/plain")
        self.assertFalse(filters.accepts({}))

    def test_010_path_filter_is_case_insensitive(self):
        filters = SearchFilters(source_path_contains="REPORTS")
        self.assertTrue(filters.accepts({"source_path": "C:/data/reports/a.pdf"}))

    def test_011_path_filter_rejects_missing_source_path(self):
        self.assertFalse(SearchFilters(source_path_contains="docs").accepts({}))

    def test_012_default_search_query_is_valid(self):
        SearchQuery("offline retrieval").validate()

    def test_013_blank_search_query_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be blank"):
            SearchQuery(" \t ").validate()

    def test_014_zero_top_k_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "between 1 and 100"):
            SearchQuery("x", top_k=0).validate()

    def test_015_top_k_above_limit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "between 1 and 100"):
            SearchQuery("x", top_k=101).validate()

    def test_016_negative_semantic_weight_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be negative"):
            SearchQuery("x", semantic_weight=-0.1).validate()

    def test_017_negative_keyword_weight_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be negative"):
            SearchQuery("x", keyword_weight=-0.1).validate()

    def test_018_zero_total_weight_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be positive"):
            SearchQuery("x", semantic_weight=0, keyword_weight=0).validate()

    def test_019_stored_record_uses_metadata_document_id(self):
        record = StoredRecord("item", "text", {"document_id": "doc"}, "space")
        self.assertEqual(record.document_id, "doc")

    def test_020_stored_record_falls_back_to_item_id(self):
        record = StoredRecord("item", "text", {}, "space")
        self.assertEqual(record.document_id, "item")

    def test_021_retrieval_hit_serializes_nested_metadata(self):
        hit = RetrievalHit(
            "i", "d", "text", 1.0, 1.0, 0.0, "s", "m", "text",
            "C:/a", "a.txt", "text/plain", 0, {"nested": {"ok": True}},
        )
        self.assertTrue(hit.to_dict()["metadata"]["nested"]["ok"])

    def test_022_search_response_serializes_hits_and_warnings(self):
        response = SearchResponse("q", (), 1.25, 0, ("warning",))
        self.assertEqual(
            response.to_dict(),
            {
                "query": "q",
                "hits": [],
                "elapsed_ms": 1.25,
                "candidate_count": 0,
                "warnings": ["warning"],
            },
        )

    def test_023_indexing_summary_success_without_failures(self):
        self.assertTrue(IndexingSummary(1, 1, (), 1, (), 1).success)

    def test_024_indexing_summary_fails_with_embedding_failure(self):
        summary = IndexingSummary(1, 1, (), 1, ({"item_id": "x"},), 0)
        self.assertFalse(summary.success)


if __name__ == "__main__":
    unittest.main()
