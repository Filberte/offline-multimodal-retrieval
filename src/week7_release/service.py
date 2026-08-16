"""Final release gate composition and JSON evidence loading."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from .models import ComplianceReport, DocumentationAudit, PreflightReport, ReleaseGate, ReleaseReadiness


def test_gate(summary: dict[str, Any], *, expected: int = 500) -> ReleaseGate:
    total = summary.get("total_tests")
    passed = bool(summary.get("all_passed")) and total == expected
    return ReleaseGate("REL-001", "Automated test suite", passed, f"{total}/{expected} catalogued; all_passed={summary.get('all_passed')}")


def coverage_gate(summary: dict[str, Any], *, minimum: float = 90.0) -> ReleaseGate:
    value = float(summary.get("coverage_percent", 0.0))
    return ReleaseGate("REL-002", "Python core coverage", value >= minimum, f"{value:.2f}% (minimum {minimum:.2f}%)")


def flutter_coverage_gate(summary: dict[str, Any], *, minimum: float = 80.0) -> ReleaseGate:
    value = float(summary.get("coverage_percent", 0.0))
    return ReleaseGate("REL-003", "Flutter source coverage", value >= minimum, f"{value:.2f}% (minimum {minimum:.2f}%)")


def compliance_gate(report: ComplianceReport) -> ReleaseGate:
    return ReleaseGate("REL-004", "Open-source compliance", report.passed, f"{len(report.records)} components; {report.blocking_findings} blocking findings")


def documentation_gate(audit: DocumentationAudit) -> ReleaseGate:
    return ReleaseGate("REL-005", "Documentation suite", audit.passed, f"{audit.present}/{audit.expected} documents; {len(audit.broken_links)} broken links")


def preflight_gate(report: PreflightReport) -> ReleaseGate:
    return ReleaseGate("REL-006", "Installation preflight", report.release_ready, f"{len(report.checks)} checks; {report.failed} blocking failures")


def artifact_gate(root: Path, required: tuple[str, ...]) -> ReleaseGate:
    missing = [name for name in required if not (root / name).is_file()]
    return ReleaseGate("REL-007", "Release artifact set", not missing, "complete" if not missing else "missing: " + ", ".join(missing))


def build_release_readiness(
    *,
    test_summary: dict[str, Any],
    core_coverage: dict[str, Any],
    flutter_coverage: dict[str, Any],
    compliance: ComplianceReport,
    documentation: DocumentationAudit,
    preflight: PreflightReport,
    artifact_root: Path,
    required_artifacts: tuple[str, ...] = (),
    version: str = "0.7.0",
    candidate: str = "rc1",
) -> ReleaseReadiness:
    """Build a complete, explicit go/no-go record for the release candidate."""

    gates = (
        test_gate(test_summary),
        coverage_gate(core_coverage),
        flutter_coverage_gate(flutter_coverage),
        compliance_gate(compliance),
        documentation_gate(documentation),
        preflight_gate(preflight),
        artifact_gate(artifact_root, required_artifacts),
    )
    return ReleaseReadiness(version, candidate, gates, date.today().isoformat())


def load_json(path: Path) -> dict[str, Any]:
    """Load an object-valued JSON evidence file with a clear validation error."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("release evidence JSON must contain an object")
    return payload


def write_readiness(report: ReleaseReadiness, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
