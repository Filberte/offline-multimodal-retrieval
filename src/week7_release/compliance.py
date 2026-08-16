"""Deterministic direct-dependency and distribution-policy checks."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Iterable

from .models import ComplianceFinding, ComplianceReport, LicenseRecord

_LICENSE_ALIASES = {
    "apache 2": "Apache-2.0",
    "apache-2.0": "Apache-2.0",
    "apache software license": "Apache-2.0",
    "bsd": "BSD-3-Clause",
    "bsd-3-clause": "BSD-3-Clause",
    "mit": "MIT",
    "mit-cmu": "MIT-CMU",
}
_APPROVED = {"Apache-2.0", "BSD-3-Clause", "MIT", "MIT-CMU", "OFL-1.1"}
_REVIEW_REQUIRED = {"CC-BY-4.0", "CC-BY-SA-4.0", "GFDL-1.3", "Apple-ML-Research"}
_REQUIRED_NOTICE_FILES = ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "MODEL_AND_DATA_LICENSES.md")


def normalize_license(value: str) -> str:
    """Return a stable SPDX-like identifier without guessing unknown licenses."""

    cleaned = " ".join(value.strip().split())
    return _LICENSE_ALIASES.get(cleaned.lower(), cleaned)


def default_inventory() -> tuple[LicenseRecord, ...]:
    """Return the reviewed direct dependency/model/dataset bill of materials."""

    return (
        LicenseRecord("Python", "3.12", "PSF-2.0", "https://docs.python.org/3/license.html"),
        LicenseRecord("Chroma", "1.5.9", "Apache-2.0", "https://github.com/chroma-core/chroma"),
        LicenseRecord("NumPy", "2.4.4", "BSD-3-Clause", "https://numpy.org/doc/stable/license.html"),
        LicenseRecord("Pillow", "12.2.0", "MIT-CMU", "https://github.com/python-pillow/Pillow"),
        LicenseRecord("pypdf", "6.14.2", "BSD-3-Clause", "https://pypdf.readthedocs.io/en/stable/meta/license.html"),
        LicenseRecord("LiteRT", "2.1.5", "Apache-2.0", "https://github.com/google-ai-edge/LiteRT"),
        LicenseRecord("Transformers", "4.57.6", "Apache-2.0", "https://github.com/huggingface/transformers"),
        LicenseRecord("OpenCLIP", "3.3.0", "MIT", "https://github.com/mlfoundations/open_clip"),
        LicenseRecord("timm", "1.0.28", "Apache-2.0", "https://github.com/huggingface/pytorch-image-models"),
        LicenseRecord("PyTorch", "2.10.0", "BSD-3-Clause", "https://github.com/pytorch/pytorch"),
        LicenseRecord("Flutter", "3.x", "BSD-3-Clause", "https://github.com/flutter/flutter"),
        LicenseRecord("Offline Retrieval CJK (Noto Sans SC subset)", "2026-08", "OFL-1.1", "https://github.com/google/fonts/tree/main/ofl/notosanssc", notes="Renamed static subset; Reserved Font Name removed; OFL text is shipped beside the asset."),
        LicenseRecord("BERT Base", "uncased", "Apache-2.0", "https://github.com/google-research/bert", component_type="model", distribution="user-supplied"),
        LicenseRecord("MobileCLIP weights", "S0/S1/S2", "Apple-ML-Research", "https://github.com/apple/ml-mobileclip", component_type="model", distribution="excluded", redistributable=False, notes="Weights are not bundled."),
        LicenseRecord("MobileCLIP DataCompDR data", "1.0", "CC-BY-NC-ND", "https://github.com/apple/ml-mobileclip", component_type="dataset", distribution="excluded", redistributable=False),
        LicenseRecord("Wikipedia validation subset", "2026-06 snapshot", "CC-BY-SA-4.0", "https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use", component_type="dataset", distribution="excluded", notes="Only aggregate metrics are included."),
        LicenseRecord("SQuAD validation subset", "2.0", "CC-BY-SA-4.0", "https://rajpurkar.github.io/SQuAD-explorer/", component_type="dataset", distribution="excluded", notes="Only aggregate metrics are included."),
        LicenseRecord("COCO validation subset", "2017", "Dataset-specific", "https://cocodataset.org/#termsofuse", component_type="dataset", distribution="excluded", redistributable=False, notes="Images and annotations are not bundled."),
        LicenseRecord("RVL-CDIP validation subset", "1.0", "Dataset-specific", "https://www.cs.cmu.edu/~aharley/rvl-cdip/", component_type="dataset", distribution="excluded", redistributable=False, notes="Document images and labels are not bundled."),
    )


def audit_inventory(records: Iterable[LicenseRecord], *, generated_at: str | None = None) -> ComplianceReport:
    """Apply allow-list, duplicate, source, and redistribution checks."""

    values = tuple(records)
    findings: list[ComplianceFinding] = []
    seen: set[str] = set()
    for record in values:
        license_id = normalize_license(record.license_id)
        if record.key in seen:
            findings.append(ComplianceFinding("OSS-001", "medium", record.name, "Duplicate direct-dependency record.", "Keep one authoritative inventory entry."))
        seen.add(record.key)
        if not record.source_url.startswith("https://"):
            findings.append(ComplianceFinding("OSS-002", "medium", record.name, "Source URL is missing or not HTTPS.", "Record an authoritative HTTPS source."))
        if record.distribution == "included" and not record.redistributable:
            findings.append(ComplianceFinding("OSS-003", "high", record.name, "A non-redistributable component is marked as included.", "Exclude it or obtain explicit redistribution rights."))
        if license_id in _REVIEW_REQUIRED and record.distribution == "included":
            findings.append(ComplianceFinding("OSS-004", "high", record.name, f"{license_id} requires distribution-specific legal review.", "Exclude from the package until approved."))
        elif license_id not in _APPROVED and license_id not in _REVIEW_REQUIRED and record.component_type == "software":
            findings.append(ComplianceFinding("OSS-005", "medium", record.name, f"Software license {license_id} is outside the reviewed allow-list.", "Complete manual policy review."))
        if record.component_type in {"model", "dataset"} and not record.notes:
            findings.append(ComplianceFinding("OSS-006", "low", record.name, "Model/dataset usage note is absent.", "Document distribution and attribution boundaries."))
    return ComplianceReport(values, tuple(findings), generated_at or date.today().isoformat())


def validate_notice_files(root: Path) -> tuple[ComplianceFinding, ...]:
    """Validate required project and third-party notice files."""

    findings: list[ComplianceFinding] = []
    for name in _REQUIRED_NOTICE_FILES:
        path = root / name
        if not path.is_file():
            findings.append(ComplianceFinding("OSS-010", "high", name, "Required compliance file is missing.", f"Add {name} to the source package root."))
        elif not path.read_text(encoding="utf-8").strip():
            findings.append(ComplianceFinding("OSS-011", "high", name, "Required compliance file is empty.", f"Populate {name} before release."))
    return tuple(findings)


def build_sbom(records: Iterable[LicenseRecord]) -> dict[str, object]:
    """Create a compact CycloneDX-inspired direct-component inventory."""

    components = []
    for record in sorted(records, key=lambda item: item.key):
        components.append({
            "type": record.component_type,
            "name": record.name,
            "version": record.version,
            "license": normalize_license(record.license_id),
            "source": record.source_url,
            "distribution": record.distribution,
        })
    return {"bomFormat": "CycloneDX-compatible-direct-inventory", "specVersion": "1.5", "components": components}


def write_compliance_artifacts(root: Path, output: Path) -> ComplianceReport:
    """Audit the project and write machine-readable inventory/evidence files."""

    output.mkdir(parents=True, exist_ok=True)
    report = audit_inventory(default_inventory())
    notice_findings = validate_notice_files(root)
    report = ComplianceReport(report.records, report.findings + notice_findings, report.generated_at)
    (output / "direct_dependency_sbom.json").write_text(json.dumps(build_sbom(report.records), indent=2, ensure_ascii=False), encoding="utf-8")
    (output / "oss_compliance_summary.json").write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return report
