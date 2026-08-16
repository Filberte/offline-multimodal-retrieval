"""Immutable Week 8 delivery, lineage, platform, and readiness records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class WeekContribution:
    week: int
    focus: str
    product_value: str
    source_paths: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    feeds_week: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetSummary:
    key: str
    display_name: str
    role: str
    expected_samples: int
    discovered_samples: int
    source_root: str
    manifest_path: str
    available: bool
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlatformCheck:
    code: str
    platform: str
    label: str
    status: str
    evidence: str
    blocking: bool = True

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["passed"] = self.passed
        return payload


@dataclass(frozen=True)
class PlatformAssessment:
    platform: str
    evidence_class: str
    checks: tuple[PlatformCheck, ...]
    decision: str
    limitations: tuple[str, ...] = ()

    @property
    def blocking_failures(self) -> tuple[PlatformCheck, ...]:
        return tuple(check for check in self.checks if check.blocking and not check.passed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "evidence_class": self.evidence_class,
            "checks": [check.to_dict() for check in self.checks],
            "decision": self.decision,
            "limitations": list(self.limitations),
            "blocking_failures": len(self.blocking_failures),
        }


@dataclass(frozen=True)
class DeliveryGate:
    code: str
    label: str
    passed: bool
    evidence: str
    blocking: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FinalReadiness:
    version: str
    generated_at: str
    gates: tuple[DeliveryGate, ...]
    external_actions: tuple[str, ...]

    @property
    def decision(self) -> str:
        return "GO" if self.gates and all(g.passed or not g.blocking for g in self.gates) else "NO-GO"

    @property
    def blocking_failures(self) -> tuple[DeliveryGate, ...]:
        return tuple(gate for gate in self.gates if gate.blocking and not gate.passed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "gates": [gate.to_dict() for gate in self.gates],
            "decision": self.decision,
            "blocking_failures": len(self.blocking_failures),
            "external_actions": list(self.external_actions),
        }
