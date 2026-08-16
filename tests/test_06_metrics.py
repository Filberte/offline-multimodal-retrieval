"""召回率、MRR、nDCG 与分位时延测试，共 8 项。"""

from __future__ import annotations

import unittest

from week4_retrieval.metrics import (
    BenchmarkCase,
    _binary_ndcg,
    _percentile,
    evaluate_retrieval,
)
from week4_retrieval.models import RetrievalHit, SearchResponse


def hit(item_id: str, document_id: str | None = None) -> RetrievalHit:
    return RetrievalHit(
        item_id,
        document_id or f"doc-{item_id}",
        "text",
        1.0,
        1.0,
        0.0,
        "space",
        "model",
        "text",
        "C:/a.txt",
        "a.txt",
        "text/plain",
        0,
        {},
    )


class StaticService:
    def __init__(self, responses):
        self.responses = responses

    def search(self, request):
        hits, latency = self.responses.get(request.text, ((), 0.0))
        return SearchResponse(request.text, tuple(hits), latency, len(hits))


class MetricsTests(unittest.TestCase):
    def test_093_empty_benchmark_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            evaluate_retrieval(StaticService({}), [])

    def test_094_case_without_relevant_ids_is_rejected(self):
        case = BenchmarkCase("bad", "q", frozenset())
        with self.assertRaisesRegex(ValueError, "no relevant ids"):
            evaluate_retrieval(StaticService({}), [case])

    def test_095_perfect_first_rank_produces_full_metrics(self):
        service = StaticService({"q": ((hit("a"),), 2.0)})
        result = evaluate_retrieval(
            service, [BenchmarkCase("c", "q", frozenset({"a"}))]
        )
        self.assertEqual(
            (result.recall_at_1, result.mrr_at_10, result.ndcg_at_10),
            (1.0, 1.0, 1.0),
        )

    def test_096_second_rank_updates_mrr_and_cutoff_recall(self):
        service = StaticService({"q": ((hit("x"), hit("a")), 2.0)})
        result = evaluate_retrieval(
            service, [BenchmarkCase("c", "q", frozenset({"a"}))]
        )
        self.assertEqual(result.recall_at_1, 0.0)
        self.assertEqual(result.recall_at_5, 1.0)
        self.assertEqual(result.mrr_at_10, 0.5)

    def test_097_complete_miss_produces_zero_relevance_metrics(self):
        service = StaticService({"q": ((hit("x"),), 2.0)})
        result = evaluate_retrieval(
            service, [BenchmarkCase("c", "q", frozenset({"a"}))]
        )
        self.assertEqual(
            (result.recall_at_10, result.mrr_at_10, result.ndcg_at_10),
            (0.0, 0.0, 0.0),
        )

    def test_098_document_id_can_satisfy_relevance_label(self):
        service = StaticService({"q": ((hit("chunk-a", "doc-a"),), 2.0)})
        result = evaluate_retrieval(
            service, [BenchmarkCase("c", "q", frozenset({"doc-a"}))]
        )
        self.assertEqual(result.recall_at_1, 1.0)

    def test_099_binary_ndcg_handles_empty_and_ranked_relevance(self):
        self.assertEqual(_binary_ndcg([], 0), 0.0)
        self.assertAlmostEqual(_binary_ndcg([False, True], 1), 1 / 1.584962500721156)

    def test_100_percentile_handles_single_and_interpolated_samples(self):
        self.assertEqual(_percentile([5.0], 0.95), 5.0)
        self.assertEqual(_percentile([1.0, 3.0], 0.5), 2.0)


if __name__ == "__main__":
    unittest.main()
