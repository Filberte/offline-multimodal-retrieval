"""Week 7 最终发布门禁与 GO/NO-GO 决策测试，共 35 项。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from week7_release.models import (
    ComplianceReport,
    DocumentationAudit,
    PreflightCheck,
    PreflightReport,
    ReleaseGate,
    ReleaseReadiness,
)
from week7_release.service import (
    artifact_gate,
    build_release_readiness,
    compliance_gate,
    coverage_gate,
    documentation_gate,
    flutter_coverage_gate,
    load_json,
    preflight_gate,
    test_gate as make_test_gate,
    write_readiness,
)


def passing_preflight():
    return PreflightReport((PreflightCheck("X", "x", "pass", "ok"),), "2026-08-13", "0.7.0")


class Week7ReleaseReadinessTests(unittest.TestCase):
    def test_406_required_failed_gate_is_blocking(self):
        self.assertTrue(ReleaseGate("X", "x", False, "bad").blocking)

    def test_407_optional_failed_gate_is_not_blocking(self):
        self.assertFalse(ReleaseGate("X", "x", False, "bad", False).blocking)

    def test_408_gate_serialization_includes_evidence(self):
        self.assertEqual(ReleaseGate("X", "x", True, "proof").to_dict()["evidence"], "proof")

    def test_409_release_with_all_gates_passes_go(self):
        report = ReleaseReadiness("0.7.0", "rc1", (ReleaseGate("X", "x", True, "ok"),), "2026-08-13")
        self.assertEqual(report.decision, "GO")

    def test_410_release_with_no_gates_is_no_go(self):
        self.assertEqual(ReleaseReadiness("0.7.0", "rc1", (), "2026-08-13").decision, "NO-GO")

    def test_411_release_with_blocker_is_no_go(self):
        report = ReleaseReadiness("0.7.0", "rc1", (ReleaseGate("X", "x", False, "bad"),), "2026-08-13")
        self.assertEqual(report.decision, "NO-GO")

    def test_412_release_counts_passed_gates(self):
        gates = (ReleaseGate("A", "a", True, "ok"), ReleaseGate("B", "b", False, "bad"))
        self.assertEqual(ReleaseReadiness("v", "c", gates, "d").passed_gates, 1)

    def test_413_release_score_is_percentage(self):
        gates = (ReleaseGate("A", "a", True, "ok"), ReleaseGate("B", "b", False, "bad"))
        self.assertEqual(ReleaseReadiness("v", "c", gates, "d").score_percent, 50.0)

    def test_414_release_serialization_includes_candidate(self):
        report = ReleaseReadiness("0.7.0", "rc7", (ReleaseGate("X", "x", True, "ok"),), "d")
        self.assertEqual(report.to_dict()["candidate"], "rc7")

    def test_415_test_gate_accepts_exactly_five_hundred_passes(self):
        self.assertTrue(make_test_gate({"total_tests": 500, "all_passed": True}).passed)

    def test_416_test_gate_rejects_wrong_count(self):
        self.assertFalse(make_test_gate({"total_tests": 499, "all_passed": True}).passed)

    def test_417_test_gate_rejects_failed_suite(self):
        self.assertFalse(make_test_gate({"total_tests": 500, "all_passed": False}).passed)

    def test_418_test_gate_supports_custom_expected_count(self):
        self.assertTrue(make_test_gate({"total_tests": 3, "all_passed": True}, expected=3).passed)

    def test_419_core_coverage_accepts_ninety_percent(self):
        self.assertTrue(coverage_gate({"coverage_percent": 90}).passed)

    def test_420_core_coverage_rejects_below_threshold(self):
        self.assertFalse(coverage_gate({"coverage_percent": 89.99}).passed)

    def test_421_core_coverage_missing_value_defaults_to_zero(self):
        self.assertFalse(coverage_gate({}).passed)

    def test_422_flutter_coverage_accepts_eighty_percent(self):
        self.assertTrue(flutter_coverage_gate({"coverage_percent": 80}).passed)

    def test_423_flutter_coverage_supports_custom_threshold(self):
        self.assertTrue(flutter_coverage_gate({"coverage_percent": 75}, minimum=70).passed)

    def test_424_compliance_gate_accepts_report_without_blocker(self):
        self.assertTrue(compliance_gate(ComplianceReport((), (), "d")).passed)

    def test_425_documentation_gate_accepts_complete_audit(self):
        self.assertTrue(documentation_gate(DocumentationAudit(2, 2)).passed)

    def test_426_documentation_gate_rejects_broken_link(self):
        self.assertFalse(documentation_gate(DocumentationAudit(1, 1, (), (), ("x",))).passed)

    def test_427_preflight_gate_accepts_ready_report(self):
        self.assertTrue(preflight_gate(passing_preflight()).passed)

    def test_428_preflight_gate_rejects_empty_report(self):
        report = PreflightReport((), "d", "v")
        self.assertFalse(preflight_gate(report).passed)

    def test_429_artifact_gate_accepts_empty_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(artifact_gate(Path(directory), ()).passed)

    def test_430_artifact_gate_accepts_present_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one.pdf").touch()
            self.assertTrue(artifact_gate(root, ("one.pdf",)).passed)

    def test_431_artifact_gate_lists_missing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            gate = artifact_gate(Path(directory), ("one.pdf", "two.zip"))
            self.assertIn("two.zip", gate.evidence)

    def test_432_full_readiness_builds_seven_gates(self):
        with tempfile.TemporaryDirectory() as directory:
            report = build_release_readiness(
                test_summary={"total_tests": 500, "all_passed": True},
                core_coverage={"coverage_percent": 95},
                flutter_coverage={"coverage_percent": 82},
                compliance=ComplianceReport((), (), "d"),
                documentation=DocumentationAudit(1, 1),
                preflight=passing_preflight(),
                artifact_root=Path(directory),
            )
            self.assertEqual(len(report.gates), 7)

    def test_433_full_passing_readiness_is_go(self):
        with tempfile.TemporaryDirectory() as directory:
            report = self._build(Path(directory))
            self.assertEqual(report.decision, "GO")

    def test_434_failed_test_gate_makes_full_readiness_no_go(self):
        with tempfile.TemporaryDirectory() as directory:
            report = self._build(Path(directory), tests={"total_tests": 499, "all_passed": True})
            self.assertEqual(report.decision, "NO-GO")

    def test_435_full_readiness_preserves_requested_version(self):
        with tempfile.TemporaryDirectory() as directory:
            report = self._build(Path(directory), version="1.2.3")
            self.assertEqual(report.version, "1.2.3")

    def test_436_load_json_reads_object(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text('{"ok": true}', encoding="utf-8")
            self.assertTrue(load_json(path)["ok"])

    def test_437_load_json_rejects_array(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "object"):
                load_json(path)

    def test_438_load_json_propagates_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text("not json", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                load_json(path)

    def test_439_write_readiness_creates_parent_and_json(self):
        with tempfile.TemporaryDirectory() as directory:
            report = ReleaseReadiness("v", "c", (ReleaseGate("X", "x", True, "ok"),), "d")
            path = Path(directory) / "nested/readiness.json"
            write_readiness(report, path)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["decision"], "GO")

    def test_440_written_readiness_has_blocking_gate_count(self):
        with tempfile.TemporaryDirectory() as directory:
            report = ReleaseReadiness("v", "c", (ReleaseGate("X", "x", False, "bad"),), "d")
            path = Path(directory) / "readiness.json"
            write_readiness(report, path)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["blocking_gates"], 1)

    def _build(self, root: Path, *, tests=None, version="0.7.0"):
        return build_release_readiness(
            test_summary=tests or {"total_tests": 500, "all_passed": True},
            core_coverage={"coverage_percent": 95},
            flutter_coverage={"coverage_percent": 82},
            compliance=ComplianceReport((), (), "d"),
            documentation=DocumentationAudit(1, 1),
            preflight=passing_preflight(),
            artifact_root=root,
            version=version,
        )


if __name__ == "__main__":
    unittest.main()
