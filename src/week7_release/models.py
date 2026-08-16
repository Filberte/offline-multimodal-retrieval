"""Immutable data contracts used by the Week 7 release gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

_SEVERITIES = {"info", "low", "medium", "high", "critical"}
_CHECK_STATUSES = {"pass", "warn", "fail"}


@dataclass(frozen=True)
class LicenseRecord:
    """A direct software, model, or dataset dependency and its distribution policy."""

    name: str
    version: str
    license_id: str
    source_url: str
    component_type: str = "software"
    distribution: str = "included"
    redistributable: bool = True
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("dependency name must not be empty")
        if not self.license_id.strip():
            raise ValueError("license identifier must not be empty")
        if self.component_type not in {"software", "model", "dataset"}:
            raise ValueError("component_type must be software, model, or dataset")
        if self.distribution not in {"included", "excluded", "user-supplied"}:
            raise ValueError("unsupported distribution policy")

    @property
    def key(self) -> str:
        return f"{self.component_type}:{self.name.lower()}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComplianceFinding:
    """One actionable open-source policy observation."""

    code: str
    severity: str
    component: str
    message: str
    remediation: str

    def __post_init__(self) -> None:
        if self.severity not in _SEVERITIES:
            raise ValueError("unsupported compliance severity")

    @property
    def blocking(self) -> bool:
        return self.severity in {"high", "critical"}

    def to_dict(self) -> dict[str, str | bool]:
        payload: dict[str, str | bool] = asdict(self)
        payload["blocking"] = self.blocking
        return payload


@dataclass(frozen=True)
class ComplianceReport:
    """Complete direct-dependency inventory and policy findings."""

    records: tuple[LicenseRecord, ...]
    findings: tuple[ComplianceFinding, ...]
    generated_at: str
    policy_version: str = "OSS-POLICY-W7-v1"

    @property
    def blocking_findings(self) -> int:
        return sum(item.blocking for item in self.findings)

    @property
    def warnings(self) -> int:
        return sum(item.severity in {"low", "medium"} for item in self.findings)

    @property
    def passed(self) -> bool:
        return self.blocking_findings == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "policy_version": self.policy_version,
            "components": len(self.records),
            "blocking_findings": self.blocking_findings,
            "warnings": self.warnings,
            "passed": self.passed,
            "records": [item.to_dict() for item in self.records],
            "findings": [item.to_dict() for item in self.findings],
        }


@dataclass(frozen=True)
class PreflightCheck:
    """One local environment or package validation check."""

    code: str
    label: str
    status: str
    detail: str
    required: bool = True

    def __post_init__(self) -> None:
        if self.status not in _CHECK_STATUSES:
            raise ValueError("status must be pass, warn, or fail")

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    @property
    def blocking(self) -> bool:
        return self.required and self.status == "fail"

    def to_dict(self) -> dict[str, str | bool]:
        payload: dict[str, str | bool] = asdict(self)
        payload["blocking"] = self.blocking
        return payload


@dataclass(frozen=True)
class PreflightReport:
    """Aggregated installation and runtime preflight report."""

    checks: tuple[PreflightCheck, ...]
    generated_at: str
    product_version: str

    @property
    def failed(self) -> int:
        return sum(item.blocking for item in self.checks)

    @property
    def warnings(self) -> int:
        return sum(item.status == "warn" for item in self.checks)

    @property
    def release_ready(self) -> bool:
        return bool(self.checks) and self.failed == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "product_version": self.product_version,
            "checks": [item.to_dict() for item in self.checks],
            "failed": self.failed,
            "warnings": self.warnings,
            "release_ready": self.release_ready,
        }


@dataclass(frozen=True)
class DocumentationEntry:
    """Expected Markdown document and its minimum structural contract."""

    path: str
    title: str
    audience: str
    required_headings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.path.endswith(".md"):
            raise ValueError("documentation path must end with .md")
        if not self.title.strip() or not self.audience.strip():
            raise ValueError("documentation title and audience are required")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["required_headings"] = list(self.required_headings)
        return payload


@dataclass(frozen=True)
class DocumentationAudit:
    """Documentation completeness and local-link validation result."""

    expected: int
    present: int
    missing_files: tuple[str, ...] = ()
    missing_headings: tuple[str, ...] = ()
    broken_links: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return (
            self.expected > 0
            and self.present == self.expected
            and not self.missing_files
            and not self.missing_headings
            and not self.broken_links
        )

    @property
    def completeness_percent(self) -> float:
        return round(self.present / self.expected * 100, 2) if self.expected else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected": self.expected,
            "present": self.present,
            "completeness_percent": self.completeness_percent,
            "passed": self.passed,
            "missing_files": list(self.missing_files),
            "missing_headings": list(self.missing_headings),
            "broken_links": list(self.broken_links),
        }


@dataclass(frozen=True)
class ReleaseGate:
    """A single final-release gate."""

    code: str
    label: str
    passed: bool
    evidence: str
    required: bool = True

    @property
    def blocking(self) -> bool:
        return self.required and not self.passed

    def to_dict(self) -> dict[str, str | bool]:
        payload: dict[str, str | bool] = asdict(self)
        payload["blocking"] = self.blocking
        return payload


@dataclass(frozen=True)
class ReleaseReadiness:
    """Final go/no-go decision with explicit evidence per gate."""

    version: str
    candidate: str
    gates: tuple[ReleaseGate, ...]
    generated_at: str

    @property
    def blocking_gates(self) -> int:
        return sum(item.blocking for item in self.gates)

    @property
    def passed_gates(self) -> int:
        return sum(item.passed for item in self.gates)

    @property
    def score_percent(self) -> float:
        return round(self.passed_gates / len(self.gates) * 100, 2) if self.gates else 0.0

    @property
    def decision(self) -> str:
        return "GO" if self.gates and self.blocking_gates == 0 else "NO-GO"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "candidate": self.candidate,
            "generated_at": self.generated_at,
            "decision": self.decision,
            "blocking_gates": self.blocking_gates,
            "score_percent": self.score_percent,
            "gates": [item.to_dict() for item in self.gates],
        }
