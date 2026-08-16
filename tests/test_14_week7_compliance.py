"""Week 7 开源、模型与数据分发合规测试，共 35 项。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from week7_release.compliance import (
    audit_inventory,
    build_sbom,
    default_inventory,
    normalize_license,
    validate_notice_files,
    write_compliance_artifacts,
)
from week7_release.models import ComplianceFinding, ComplianceReport, LicenseRecord


def software(name="Example", license_id="MIT", **kwargs):
    return LicenseRecord(name, "1.0", license_id, "https://example.test/source", **kwargs)


class Week7ComplianceTests(unittest.TestCase):
    def test_301_license_record_rejects_empty_name(self):
        with self.assertRaisesRegex(ValueError, "name"):
            software(" ")

    def test_302_license_record_rejects_empty_license(self):
        with self.assertRaisesRegex(ValueError, "license"):
            software(license_id=" ")

    def test_303_license_record_rejects_unknown_component_type(self):
        with self.assertRaisesRegex(ValueError, "component_type"):
            software(component_type="firmware")

    def test_304_license_record_rejects_unknown_distribution(self):
        with self.assertRaisesRegex(ValueError, "distribution"):
            software(distribution="maybe")

    def test_305_license_record_key_is_stable_and_lowercase(self):
        self.assertEqual(software("NumPy").key, "software:numpy")

    def test_306_license_record_serializes_all_policy_fields(self):
        payload = software(notes="reviewed").to_dict()
        self.assertEqual((payload["version"], payload["notes"]), ("1.0", "reviewed"))

    def test_307_finding_rejects_unsupported_severity(self):
        with self.assertRaisesRegex(ValueError, "severity"):
            ComplianceFinding("X", "urgent", "x", "x", "x")

    def test_308_high_finding_is_blocking(self):
        self.assertTrue(ComplianceFinding("X", "high", "x", "x", "x").blocking)

    def test_309_medium_finding_is_not_blocking(self):
        self.assertFalse(ComplianceFinding("X", "medium", "x", "x", "x").blocking)

    def test_310_report_counts_blocking_findings(self):
        findings = (ComplianceFinding("X", "critical", "x", "x", "x"),)
        self.assertEqual(ComplianceReport((), findings, "2026-08-13").blocking_findings, 1)

    def test_311_report_counts_low_and_medium_warnings(self):
        findings = tuple(ComplianceFinding(str(i), level, "x", "x", "x") for i, level in enumerate(("low", "medium", "info")))
        self.assertEqual(ComplianceReport((), findings, "2026-08-13").warnings, 2)

    def test_312_report_without_blockers_passes(self):
        report = ComplianceReport((), (ComplianceFinding("X", "low", "x", "x", "x"),), "2026-08-13")
        self.assertTrue(report.passed)

    def test_313_report_serialization_includes_policy_version(self):
        self.assertEqual(ComplianceReport((), (), "2026-08-13").to_dict()["policy_version"], "OSS-POLICY-W7-v1")

    def test_314_normalize_apache_alias(self):
        self.assertEqual(normalize_license(" Apache 2 "), "Apache-2.0")

    def test_315_normalize_bsd_alias(self):
        self.assertEqual(normalize_license("BSD"), "BSD-3-Clause")

    def test_316_normalize_mit_alias(self):
        self.assertEqual(normalize_license("mit"), "MIT")

    def test_317_normalize_unknown_preserves_cleaned_value(self):
        self.assertEqual(normalize_license("  Custom   Terms  "), "Custom Terms")

    def test_318_default_inventory_has_nineteen_direct_records(self):
        self.assertEqual(len(default_inventory()), 19)

    def test_319_default_inventory_separates_software_models_and_data(self):
        types = {item.component_type for item in default_inventory()}
        self.assertEqual(types, {"software", "model", "dataset"})

    def test_320_mobileclip_weights_are_excluded(self):
        record = next(item for item in default_inventory() if item.name == "MobileCLIP weights")
        self.assertEqual((record.distribution, record.redistributable), ("excluded", False))

    def test_321_default_inventory_has_no_included_nonredistributable_component(self):
        self.assertFalse(any(item.distribution == "included" and not item.redistributable for item in default_inventory()))

    def test_322_default_inventory_passes_blocking_policy(self):
        self.assertTrue(audit_inventory(default_inventory(), generated_at="2026-08-13").passed)

    def test_323_duplicate_record_creates_medium_finding(self):
        item = software()
        report = audit_inventory((item, item))
        self.assertIn(("OSS-001", "medium"), {(x.code, x.severity) for x in report.findings})

    def test_324_non_https_source_creates_finding(self):
        item = LicenseRecord("x", "1", "MIT", "http://example.test")
        self.assertIn("OSS-002", {x.code for x in audit_inventory((item,)).findings})

    def test_325_included_nonredistributable_component_blocks(self):
        item = software(redistributable=False)
        report = audit_inventory((item,))
        self.assertFalse(report.passed)

    def test_326_included_review_required_license_blocks(self):
        item = software(license_id="Apple-ML-Research")
        self.assertIn("OSS-004", {x.code for x in audit_inventory((item,)).findings})

    def test_327_unknown_software_license_requires_manual_review(self):
        report = audit_inventory((software(license_id="Custom"),))
        self.assertIn("OSS-005", {x.code for x in report.findings})

    def test_328_model_without_usage_note_creates_low_finding(self):
        item = software(component_type="model", distribution="excluded")
        finding = next(x for x in audit_inventory((item,)).findings if x.code == "OSS-006")
        self.assertEqual(finding.severity, "low")

    def test_329_missing_notice_files_create_four_blockers(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(len(validate_notice_files(Path(directory))), 4)

    def test_330_empty_notice_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "MODEL_AND_DATA_LICENSES.md"):
                (root / name).write_text("ok", encoding="utf-8")
            (root / "NOTICE").write_text(" ", encoding="utf-8")
            self.assertEqual(validate_notice_files(root)[0].code, "OSS-011")

    def test_331_populated_notice_files_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "MODEL_AND_DATA_LICENSES.md"):
                (root / name).write_text("reviewed", encoding="utf-8")
            self.assertEqual(validate_notice_files(root), ())

    def test_332_sbom_is_sorted_by_component_key(self):
        payload = build_sbom((software("Zulu"), software("Alpha")))
        self.assertEqual([x["name"] for x in payload["components"]], ["Alpha", "Zulu"])

    def test_333_sbom_normalizes_license_identifiers(self):
        component = build_sbom((software(license_id="apache 2"),))["components"][0]
        self.assertEqual(component["license"], "Apache-2.0")

    def test_334_write_artifacts_creates_machine_readable_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "MODEL_AND_DATA_LICENSES.md"):
                (root / name).write_text("reviewed", encoding="utf-8")
            report = write_compliance_artifacts(root, root / "reports")
            self.assertTrue(report.passed)
            self.assertTrue((root / "reports/direct_dependency_sbom.json").is_file())

    def test_335_written_summary_component_count_matches_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "MODEL_AND_DATA_LICENSES.md"):
                (root / name).write_text("reviewed", encoding="utf-8")
            write_compliance_artifacts(root, root / "reports")
            payload = json.loads((root / "reports/oss_compliance_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["components"], 19)


if __name__ == "__main__":
    unittest.main()
