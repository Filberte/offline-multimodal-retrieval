"""Final delivery GO/NO-GO aggregation tests, TC-576 through TC-600."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from week8_delivery.models import DatasetSummary, DeliveryGate, FinalReadiness, PlatformAssessment, PlatformCheck
from week8_delivery.readiness import build_final_readiness


def _datasets(available: bool = True):
    return tuple(DatasetSummary(key, key, "role", 1, 1, "root", "manifest", available) for key in ("squad", "coco", "rvl", "wiki"))


def _platforms(windows: str = "GO", simulations_pass: bool = True):
    check = PlatformCheck("x", "p", "l", "pass" if simulations_pass else "fail", "e")
    return (PlatformAssessment("Windows", "real", (check,), windows), PlatformAssessment("macOS", "simulation", (check,), "PENDING"), PlatformAssessment("Linux", "simulation", (check,), "PENDING"))


def _tests(*, total: int = 600, all_passed: bool = True, core: float = 95, flutter: float = 84):
    return {"total_tests": total, "all_passed": all_passed, "continuous_ids_tc_001_to_tc_600": total == 600, "core": {"coverage_percent": core}, "flutter": {"coverage_percent": flutter}}


def _build(root: Path, **kwargs):
    lineage = kwargs.pop("lineage", True)
    datasets = kwargs.pop("datasets", _datasets())
    with patch("week8_delivery.readiness.validate_lineage", return_value={"all_contributions_present": lineage}), patch("week8_delivery.readiness.dataset_inventory", return_value=datasets):
        return build_final_readiness(root, **kwargs)


class Week8ReadinessTests(unittest.TestCase):
    def test_576_delivery_gate_serializes(self):
        self.assertTrue(DeliveryGate("x", "l", True, "e").to_dict()["passed"])

    def test_577_final_readiness_go_with_passing_gate(self):
        self.assertEqual(FinalReadiness("1", "d", (DeliveryGate("x", "l", True, "e"),), ()).decision, "GO")

    def test_578_final_readiness_no_go_without_gates(self):
        self.assertEqual(FinalReadiness("1", "d", (), ()).decision, "NO-GO")

    def test_579_final_readiness_no_go_on_blocker(self):
        self.assertEqual(FinalReadiness("1", "d", (DeliveryGate("x", "l", False, "e"),), ()).decision, "NO-GO")

    def test_580_nonblocking_failure_preserves_go(self):
        gates = (DeliveryGate("x", "l", True, "e"), DeliveryGate("y", "l", False, "e", False))
        self.assertEqual(FinalReadiness("1", "d", gates, ()).decision, "GO")

    def test_581_blocking_failures_are_counted(self):
        item = FinalReadiness("1", "d", (DeliveryGate("x", "l", False, "e"),), ())
        self.assertEqual(len(item.blocking_failures), 1)

    def test_582_readiness_version_is_one_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(_build(Path(temp), test_summary=_tests(), platforms=_platforms()).version, "1.0.0")

    def test_583_readiness_has_ten_gates(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(len(_build(Path(temp), test_summary=_tests(), platforms=_platforms()).gates), 10)

    def test_584_complete_internal_delivery_is_go(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(_build(Path(temp), test_summary=_tests(), platforms=_platforms()).decision, "GO")

    def test_585_lineage_failure_blocks_release(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(_build(Path(temp), test_summary=_tests(), platforms=_platforms(), lineage=False).decision, "NO-GO")

    def test_586_dataset_failure_blocks_release(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(_build(Path(temp), test_summary=_tests(), platforms=_platforms(), datasets=_datasets(False)).decision, "NO-GO")

    def test_587_test_count_must_equal_six_hundred(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(_build(Path(temp), test_summary=_tests(total=599), platforms=_platforms()).decision, "NO-GO")

    def test_588_failed_suite_blocks_release(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(_build(Path(temp), test_summary=_tests(all_passed=False), platforms=_platforms()).decision, "NO-GO")

    def test_589_core_coverage_below_ninety_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(_build(Path(temp), test_summary=_tests(core=89.99), platforms=_platforms()).decision, "NO-GO")

    def test_590_core_coverage_at_ninety_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            result = _build(Path(temp), test_summary=_tests(core=90), platforms=_platforms())
            self.assertTrue(next(g for g in result.gates if g.code == "W8-G04").passed)

    def test_591_flutter_coverage_below_eighty_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(_build(Path(temp), test_summary=_tests(flutter=79.99), platforms=_platforms()).decision, "NO-GO")

    def test_592_flutter_coverage_at_eighty_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            result = _build(Path(temp), test_summary=_tests(flutter=80), platforms=_platforms())
            self.assertTrue(next(g for g in result.gates if g.code == "W8-G05").passed)

    def test_593_windows_no_go_blocks_release(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(_build(Path(temp), test_summary=_tests(), platforms=_platforms(windows="NO-GO")).decision, "NO-GO")

    def test_594_simulation_contract_failure_blocks_release(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(_build(Path(temp), test_summary=_tests(), platforms=_platforms(simulations_pass=False)).decision, "NO-GO")

    def test_595_missing_required_document_blocks_release(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(_build(Path(temp), test_summary=_tests(), platforms=_platforms(), required_documents=("missing.pdf",)).decision, "NO-GO")

    def test_596_present_required_document_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / "present.pdf").write_bytes(b"pdf")
            result = _build(root, test_summary=_tests(), platforms=_platforms(), required_documents=("present.pdf",))
            self.assertTrue(next(g for g in result.gates if g.code == "W8-G08").passed)

    def test_597_github_gate_is_nonblocking(self):
        with tempfile.TemporaryDirectory() as temp:
            gate = next(g for g in _build(Path(temp), test_summary=_tests(), platforms=_platforms()).gates if g.code == "W8-G09")
            self.assertFalse(gate.blocking)

    def test_598_video_gate_is_nonblocking_during_owner_handoff(self):
        with tempfile.TemporaryDirectory() as temp:
            gate = next(g for g in _build(Path(temp), test_summary=_tests(), platforms=_platforms()).gates if g.code == "W8-G10")
            self.assertFalse(gate.blocking)

    def test_599_external_actions_include_video(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertIn("视频", " ".join(_build(Path(temp), test_summary=_tests(), platforms=_platforms()).external_actions))

    def test_600_final_readiness_serializes_decision(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(_build(Path(temp), test_summary=_tests(), platforms=_platforms()).to_dict()["decision"], "GO")
