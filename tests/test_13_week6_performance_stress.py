"""Week 6 性能、内存和压力工具测试，共 30 项。"""

from __future__ import annotations

import unittest

from week6_integration.models import (
    RuntimeMetrics,
    SecurityFinding,
    SecurityReview,
)
from week6_integration.performance import (
    improvement_percent,
    measure_operation,
    percentile,
    profile_memory,
    run_stress,
)


class PerformanceStressTests(unittest.TestCase):
    def test_241_percentile_rejects_empty_values(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            percentile([], 50)

    def test_242_percentile_rejects_negative_percent(self):
        with self.assertRaises(ValueError):
            percentile([1], -1)

    def test_243_percentile_rejects_percent_over_hundred(self):
        with self.assertRaises(ValueError):
            percentile([1], 101)

    def test_244_percentile_single_value_is_stable(self):
        self.assertEqual(percentile([7], 95), 7)

    def test_245_percentile_zero_returns_minimum(self):
        self.assertEqual(percentile([3, 1, 2], 0), 1)

    def test_246_percentile_hundred_returns_maximum(self):
        self.assertEqual(percentile([3, 1, 2], 100), 3)

    def test_247_percentile_fifty_returns_median(self):
        self.assertEqual(percentile([1, 2, 3], 50), 2)

    def test_248_percentile_linearly_interpolates(self):
        self.assertEqual(percentile([0, 10], 25), 2.5)

    def test_249_measure_rejects_zero_iterations(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            measure_operation(lambda: None, iterations=0)

    def test_250_measure_rejects_negative_warmups(self):
        with self.assertRaisesRegex(ValueError, "must not be negative"):
            measure_operation(lambda: None, iterations=1, warmups=-1)

    def test_251_measure_runs_warmups_and_iterations(self):
        calls = []
        measure_operation(lambda: calls.append(1), iterations=4, warmups=2)
        self.assertEqual(len(calls), 6)

    def test_252_measure_minimum_does_not_exceed_maximum(self):
        stats = measure_operation(lambda: sum(range(10)), iterations=5)
        self.assertLessEqual(stats.minimum_ms, stats.maximum_ms)

    def test_253_measure_reports_positive_throughput(self):
        stats = measure_operation(lambda: None, iterations=5, warmups=0)
        self.assertGreater(stats.throughput_per_second, 0)

    def test_254_measure_serializes_latency_fields(self):
        payload = measure_operation(lambda: None, iterations=3).to_dict()
        self.assertEqual(payload["iterations"], 3)
        self.assertIn("p95_ms", payload)

    def test_255_improvement_rejects_zero_baseline(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            improvement_percent(0, 1)

    def test_256_improvement_reports_fifty_percent(self):
        self.assertEqual(improvement_percent(10, 5), 50)

    def test_257_improvement_can_report_regression(self):
        self.assertEqual(improvement_percent(10, 12), -20)

    def test_258_memory_profile_returns_operation_value(self):
        result = profile_memory(lambda: [1, 2, 3])
        self.assertEqual(result.value, [1, 2, 3])

    def test_259_memory_peak_is_not_below_current(self):
        result = profile_memory(lambda: bytearray(1024))
        self.assertGreaterEqual(result.peak_bytes, result.current_bytes)

    def test_260_stress_rejects_negative_operations(self):
        with self.assertRaisesRegex(ValueError, "must not be negative"):
            run_stress(lambda _: None, operations=-1, concurrency=1)

    def test_261_stress_rejects_zero_concurrency(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            run_stress(lambda _: None, operations=1, concurrency=0)

    def test_262_zero_operation_stress_is_successful(self):
        result = run_stress(lambda _: None, operations=0, concurrency=4)
        self.assertEqual((result.succeeded, result.success_rate), (0, 1.0))

    def test_263_parallel_stress_completes_two_hundred_operations(self):
        completed = []
        result = run_stress(
            lambda index: completed.append(index),
            operations=200,
            concurrency=8,
        )
        self.assertEqual((len(completed), result.succeeded), (200, 200))

    def test_264_stress_counts_operation_failures(self):
        def operation(index):
            if index % 2 == 0:
                raise RuntimeError("planned")

        result = run_stress(operation, operations=10, concurrency=3)
        self.assertEqual((result.succeeded, result.failed), (5, 5))

    def test_265_stress_success_rate_reflects_failures(self):
        def operation(index):
            if index == 0:
                raise RuntimeError("planned")

        result = run_stress(operation, operations=4, concurrency=2)
        self.assertEqual(result.success_rate, 0.75)

    def test_266_stress_preserves_requested_concurrency(self):
        result = run_stress(lambda _: None, operations=3, concurrency=2)
        self.assertEqual(result.concurrency, 2)

    def test_267_stress_serialization_includes_success_rate(self):
        payload = run_stress(
            lambda _: None,
            operations=3,
            concurrency=2,
        ).to_dict()
        self.assertEqual(payload["success_rate"], 1.0)

    def test_268_runtime_metrics_average_is_zero_without_search(self):
        metrics = RuntimeMetrics(0, 0, 0, 0, 0, 0, 0.0)
        self.assertEqual(metrics.average_search_ms, 0)

    def test_269_runtime_metrics_average_uses_operation_count(self):
        metrics = RuntimeMetrics(0, 0, 0, 4, 1, 0, 20.0)
        payload = metrics.to_dict()
        self.assertEqual(payload["average_search_ms"], 5.0)

    def test_270_security_review_serializes_findings(self):
        finding = SecurityFinding("SEC-TEST", "low", "a.py", "test")
        review = SecurityReview(1, (finding,))
        payload = review.to_dict()
        self.assertEqual(payload["findings"][0]["code"], "SEC-TEST")
        self.assertTrue(payload["passed"])


if __name__ == "__main__":
    unittest.main()
