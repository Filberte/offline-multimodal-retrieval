"""混合排序、归一化和稳定次级排序测试，共 18 项。"""

from __future__ import annotations

import unittest

from week4_retrieval.keyword import KeywordMatch
from week4_retrieval.models import SemanticCandidate
from week4_retrieval.ranking import HybridRanker

from tests._support import make_record


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.ranker = HybridRanker()

    def rank(self, semantic=(), keyword=(), sw=0.7, kw=0.3, top_k=10):
        return self.ranker.rank(
            semantic=semantic,
            keyword=keyword,
            semantic_weight=sw,
            keyword_weight=kw,
            top_k=top_k,
        )

    def test_041_zero_top_k_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            self.rank(top_k=0)

    def test_042_negative_semantic_weight_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid ranking"):
            self.rank(sw=-1, kw=1)

    def test_043_negative_keyword_weight_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid ranking"):
            self.rank(sw=1, kw=-1)

    def test_044_zero_total_weight_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid ranking"):
            self.rank(sw=0, kw=0)

    def test_045_weights_are_normalized_before_fusion(self):
        a, b = make_record("a"), make_record("b")
        hits = self.rank(
            semantic=(SemanticCandidate(a, 1.0), SemanticCandidate(b, 0.0)),
            keyword=(KeywordMatch(b, 2.0),),
            sw=7,
            kw=3,
        )
        self.assertAlmostEqual(hits[0].score, 0.7)

    def test_046_single_positive_semantic_candidate_scores_one(self):
        hit = self.rank(
            semantic=(SemanticCandidate(make_record("a"), 0.2),),
            sw=1,
            kw=0,
        )[0]
        self.assertEqual(hit.score, 1.0)

    def test_047_single_negative_semantic_candidate_scores_zero(self):
        hit = self.rank(
            semantic=(SemanticCandidate(make_record("a"), -0.2),),
            sw=1,
            kw=0,
        )[0]
        self.assertEqual(hit.score, 0.0)

    def test_048_equal_positive_semantic_scores_are_all_one(self):
        hits = self.rank(
            semantic=(
                SemanticCandidate(make_record("a"), 0.2),
                SemanticCandidate(make_record("b"), 0.2),
            ),
            sw=1,
            kw=0,
        )
        self.assertTrue(all(hit.semantic_score == 1.0 for hit in hits))

    def test_049_equal_zero_semantic_scores_are_all_zero(self):
        hits = self.rank(
            semantic=(
                SemanticCandidate(make_record("a"), 0.0),
                SemanticCandidate(make_record("b"), 0.0),
            ),
            sw=1,
            kw=0,
        )
        self.assertTrue(all(hit.semantic_score == 0.0 for hit in hits))

    def test_050_semantic_minmax_normalization_bounds_scores(self):
        hits = self.rank(
            semantic=(
                SemanticCandidate(make_record("a"), -1.0),
                SemanticCandidate(make_record("b"), 0.0),
                SemanticCandidate(make_record("c"), 1.0),
            ),
            sw=1,
            kw=0,
        )
        self.assertEqual([hit.semantic_score for hit in hits], [1.0, 0.5, 0.0])

    def test_051_keyword_scores_are_normalized_by_positive_maximum(self):
        a, b = make_record("a"), make_record("b")
        hits = self.rank(
            keyword=(KeywordMatch(a, 4.0), KeywordMatch(b, 2.0)),
            sw=0,
            kw=1,
        )
        self.assertEqual([hit.keyword_score for hit in hits], [1.0, 0.5])

    def test_052_nonpositive_keyword_scores_are_bounded_at_zero(self):
        hits = self.rank(
            keyword=(
                KeywordMatch(make_record("a"), 0.0),
                KeywordMatch(make_record("b"), -2.0),
            ),
            sw=0,
            kw=1,
        )
        self.assertTrue(all(hit.keyword_score == 0.0 for hit in hits))

    def test_053_duplicate_semantic_candidates_keep_highest_score(self):
        record = make_record("a")
        hit = self.rank(
            semantic=(
                SemanticCandidate(record, 0.1),
                SemanticCandidate(record, 0.8),
            ),
            sw=1,
            kw=0,
        )[0]
        self.assertEqual(hit.semantic_score, 1.0)

    def test_054_duplicate_keyword_candidates_keep_highest_score(self):
        record = make_record("a")
        hit = self.rank(
            keyword=(KeywordMatch(record, 1.0), KeywordMatch(record, 5.0)),
            sw=0,
            kw=1,
        )[0]
        self.assertEqual(hit.keyword_score, 1.0)

    def test_055_same_item_id_in_different_spaces_remains_distinct(self):
        text = make_record("same", space="bert")
        image = make_record("same", space="mobileclip", modality="image")
        hits = self.rank(
            semantic=(SemanticCandidate(text, 0.8), SemanticCandidate(image, 0.7))
        )
        self.assertEqual({hit.space for hit in hits}, {"bert", "mobileclip"})

    def test_056_top_k_truncates_ranked_results(self):
        semantic = tuple(
            SemanticCandidate(make_record(str(index)), float(index))
            for index in range(5)
        )
        self.assertEqual(len(self.rank(semantic=semantic, top_k=2)), 2)

    def test_057_tied_scores_use_file_name_then_item_id(self):
        b = make_record("b", file_name="z.txt")
        a = make_record("a", file_name="a.txt")
        hits = self.rank(
            semantic=(SemanticCandidate(b, 1.0), SemanticCandidate(a, 1.0)),
            sw=1,
            kw=0,
        )
        self.assertEqual([hit.item_id for hit in hits], ["a", "b"])

    def test_058_invalid_chunk_index_is_returned_as_none(self):
        hit = self.rank(
            semantic=(SemanticCandidate(make_record("a", chunk_index="bad"), 1.0),),
            sw=1,
            kw=0,
        )[0]
        self.assertIsNone(hit.chunk_index)


if __name__ == "__main__":
    unittest.main()
