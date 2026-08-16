"""确定性分词与 BM25 关键词检索测试，共 16 项。"""

from __future__ import annotations

import unittest

from week4_retrieval.keyword import BM25Index, tokenize

from tests._support import make_record


class KeywordTests(unittest.TestCase):
    def test_025_tokenize_lowercases_english(self):
        self.assertEqual(tokenize("Offline SEARCH"), ("offline", "search"))

    def test_026_tokenize_preserves_apostrophe_and_underscore(self):
        self.assertEqual(tokenize("don't file_name"), ("don't", "file_name"))

    def test_027_tokenize_preserves_numbers(self):
        self.assertEqual(tokenize("Week4 2026"), ("week4", "2026"))

    def test_028_tokenize_splits_chinese_into_characters(self):
        self.assertEqual(tokenize("本地检索"), ("本", "地", "检", "索"))

    def test_029_tokenize_empty_text_returns_empty_tuple(self):
        self.assertEqual(tokenize("... \t"), ())

    def test_030_bm25_rejects_nonpositive_k1(self):
        with self.assertRaisesRegex(ValueError, "invalid BM25"):
            BM25Index((), k1=0)

    def test_031_bm25_rejects_below_range_b(self):
        with self.assertRaisesRegex(ValueError, "invalid BM25"):
            BM25Index((), b=-0.1)

    def test_032_bm25_rejects_above_range_b(self):
        with self.assertRaisesRegex(ValueError, "invalid BM25"):
            BM25Index((), b=1.1)

    def test_033_bm25_ignores_blank_documents(self):
        index = BM25Index((make_record("a", " "), make_record("b", "offline")))
        self.assertEqual(index.document_count, 1)

    def test_034_empty_bm25_index_returns_no_matches(self):
        self.assertEqual(BM25Index(()).search("offline"), ())

    def test_035_blank_query_returns_no_matches(self):
        index = BM25Index((make_record("a", "offline"),))
        self.assertEqual(index.search("   "), ())

    def test_036_unmatched_query_returns_no_matches(self):
        index = BM25Index((make_record("a", "offline"),))
        self.assertEqual(index.search("cloud"), ())

    def test_037_exact_terms_rank_relevant_document_first(self):
        index = BM25Index(
            (
                make_record("a", "offline private local processing"),
                make_record("b", "cloud network synchronization"),
            )
        )
        self.assertEqual(index.search("offline local")[0].record.item_id, "a")

    def test_038_search_limit_truncates_matches(self):
        index = BM25Index(
            (
                make_record("a", "local search"),
                make_record("b", "local storage"),
                make_record("c", "local privacy"),
            )
        )
        self.assertEqual(len(index.search("local", limit=2)), 2)

    def test_039_equal_scores_use_item_id_for_stable_order(self):
        index = BM25Index(
            (make_record("b", "local"), make_record("a", "local"))
        )
        self.assertEqual([m.record.item_id for m in index.search("local")], ["a", "b"])

    def test_040_repeated_query_term_increases_score(self):
        index = BM25Index((make_record("a", "local search"),))
        single = index.search("local")[0].score
        repeated = index.search("local local")[0].score
        self.assertGreater(repeated, single)


if __name__ == "__main__":
    unittest.main()
