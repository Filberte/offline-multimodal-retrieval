"""Chroma 检索适配器与容错转换测试，共 16 项。"""

from __future__ import annotations

import unittest

from week4_retrieval.repository import (
    ChromaRetrievalRepository,
    _first_query_row,
    _safe_index,
)


class FakeCollection:
    def __init__(self):
        self.payload = {
            "ids": ["a"],
            "documents": ["alpha"],
            "metadatas": [{"document_id": "doc-a"}],
        }
        self.kwargs = None

    def get(self, **kwargs):
        self.kwargs = kwargs
        return self.payload


class FakeStore:
    def __init__(self):
        self._dimensions = {"space": 2}
        self.collection = FakeCollection()
        self.query_payload = {
            "ids": [["a"]],
            "documents": [["alpha"]],
            "metadatas": [[{"document_id": "doc-a"}]],
            "distances": [[0.25]],
        }
        self.query_kwargs = None
        self.upsert_values = None
        self.deleted = None
        self.collection_args = None

    def query(self, **kwargs):
        self.query_kwargs = kwargs
        return self.query_payload

    def upsert(self, vectors):
        self.upsert_values = tuple(vectors)
        return len(self.upsert_values)

    def delete(self, **kwargs):
        self.deleted = kwargs

    def _collection(self, space, dimension):
        self.collection_args = (space, dimension)
        return self.collection


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeStore()
        self.repository = ChromaRetrievalRepository(self.store)

    def test_059_constructor_keeps_store_reference(self):
        self.assertIs(self.repository.store, self.store)

    def test_060_upsert_delegates_all_vectors(self):
        self.assertEqual(self.repository.upsert((1, 2)), 2)
        self.assertEqual(self.store.upsert_values, (1, 2))

    def test_061_semantic_search_passes_query_arguments(self):
        self.repository.semantic_search(
            space="space", query_embedding=(1.0, 0.0), n_results=3, where={"x": 1}
        )
        self.assertEqual(self.store.query_kwargs["n_results"], 3)
        self.assertEqual(self.store.query_kwargs["where"], {"x": 1})

    def test_062_semantic_search_converts_cosine_distance(self):
        candidate = self.repository.semantic_search(
            space="space", query_embedding=(1.0, 0.0), n_results=1
        )[0]
        self.assertAlmostEqual(candidate.similarity, 0.75)

    def test_063_semantic_similarity_is_clamped_to_negative_one(self):
        self.store.query_payload["distances"] = [[3.0]]
        candidate = self.repository.semantic_search(
            space="space", query_embedding=(1.0, 0.0), n_results=1
        )[0]
        self.assertEqual(candidate.similarity, -1.0)

    def test_064_semantic_similarity_is_clamped_to_positive_one(self):
        self.store.query_payload["distances"] = [[-2.0]]
        candidate = self.repository.semantic_search(
            space="space", query_embedding=(1.0, 0.0), n_results=1
        )[0]
        self.assertEqual(candidate.similarity, 1.0)

    def test_065_missing_query_fields_use_safe_defaults(self):
        self.store.query_payload = {"ids": [["a"]]}
        candidate = self.repository.semantic_search(
            space="space", query_embedding=(1.0, 0.0), n_results=1
        )[0]
        self.assertEqual(candidate.record.document, "")
        self.assertEqual(candidate.record.metadata, {})
        self.assertEqual(candidate.similarity, 0.0)

    def test_066_empty_query_row_returns_no_candidates(self):
        self.store.query_payload = {"ids": [[]]}
        self.assertEqual(
            self.repository.semantic_search(
                space="space", query_embedding=(0.0, 1.0), n_results=1
            ),
            (),
        )

    def test_067_first_query_row_extracts_nested_row(self):
        self.assertEqual(_first_query_row([["a", "b"]]), ["a", "b"])

    def test_068_first_query_row_handles_none(self):
        self.assertEqual(_first_query_row(None), [])

    def test_069_safe_index_returns_default_for_short_array(self):
        self.assertEqual(_safe_index([], 1, "fallback"), "fallback")

    def test_070_scan_rejects_unknown_space(self):
        with self.assertRaisesRegex(ValueError, "unknown vector space"):
            self.repository.scan(space="missing")

    def test_071_scan_rejects_nonpositive_limit(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            self.repository.scan(space="space", limit=0)

    def test_072_scan_without_filters_uses_expected_include_fields(self):
        records = self.repository.scan(space="space")
        self.assertEqual(records[0].document_id, "doc-a")
        self.assertEqual(
            self.store.collection.kwargs,
            {"include": ["metadatas", "documents"]},
        )

    def test_073_scan_passes_where_and_limit(self):
        self.repository.scan(space="space", where={"x": 1}, limit=5)
        self.assertEqual(self.store.collection.kwargs["where"], {"x": 1})
        self.assertEqual(self.store.collection.kwargs["limit"], 5)

    def test_074_delete_delegates_space_and_ids(self):
        self.repository.delete(space="space", ids=["a", "b"])
        self.assertEqual(self.store.deleted, {"space": "space", "ids": ["a", "b"]})


if __name__ == "__main__":
    unittest.main()
