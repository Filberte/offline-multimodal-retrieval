"""Portable local preflight checks for installation and release packaging."""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import date
from pathlib import Path

from .models import PreflightCheck, PreflightReport

REQUIRED_PROJECT_PATHS = (
    "src/week4_retrieval",
    "src/week6_integration",
    "src/week7_release",
    "app/offline_retrieval_ui/pubspec.yaml",
    "docs/INSTALLATION.md",
    "docs/USER_GUIDE.md",
    "LICENSE",
    "NOTICE",
)


def python_version_check(version: tuple[int, ...] | None = None) -> PreflightCheck:
    """Require Python 3.12+ because the release metadata declares that floor."""

    actual = version or tuple(sys.version_info[:3])
    passed = actual >= (3, 12)
    return PreflightCheck("ENV-001", "Python version", "pass" if passed else "fail", ".".join(map(str, actual)), True)


def path_check(root: Path, relative: str, *, required: bool = True) -> PreflightCheck:
    """Check that a project-relative file or directory exists."""

    exists = (root / relative).exists()
    status = "pass" if exists else ("fail" if required else "warn")
    return PreflightCheck("PKG-001", f"Path: {relative}", status, "present" if exists else "missing", required)


def writable_directory_check(path: Path) -> PreflightCheck:
    """Perform a real create/delete probe without modifying user content."""

    try:
        path.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(prefix="week7-preflight-", dir=path)
        os.close(handle)
        Path(temporary).unlink()
        return PreflightCheck("ENV-002", "Local data directory writable", "pass", str(path), True)
    except OSError as exc:
        return PreflightCheck("ENV-002", "Local data directory writable", "fail", str(exc), True)


def offline_configuration_check(root: Path) -> PreflightCheck:
    """Reject production Python sources that bind network listeners."""

    suspicious: list[str] = []
    src = root / "src"
    if src.exists():
        for path in src.rglob("*.py"):
            # The scanner implementation contains the signatures it detects.
            if path.resolve() == Path(__file__).resolve():
                continue
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            if "http.server" in text or ".listen(" in text or "0.0.0.0" in text:
                suspicious.append(str(path.relative_to(root)))
    detail = "no listener patterns" if not suspicious else ", ".join(suspicious)
    return PreflightCheck("SEC-001", "Offline-only transport", "pass" if not suspicious else "fail", detail, True)


def model_boundary_check(root: Path) -> PreflightCheck:
    """Ensure restricted or very large model artifacts are not bundled."""

    extensions = {".pt", ".pth", ".ckpt", ".onnx", ".tflite", ".safetensors"}
    bundled = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in extensions]
    detail = "no model weights bundled" if not bundled else ", ".join(str(path.relative_to(root)) for path in bundled[:8])
    return PreflightCheck("OSS-020", "Model redistribution boundary", "pass" if not bundled else "fail", detail, True)


def generated_artifact_check(root: Path) -> PreflightCheck:
    """Warn if mutable caches or compiled outputs remain in the source tree."""

    forbidden = {"__pycache__", ".dart_tool", "coverage", "build"}
    found = sorted({path.name for path in root.rglob("*") if path.is_dir() and path.name in forbidden})
    return PreflightCheck("PKG-002", "Source package cleanliness", "pass" if not found else "warn", "clean" if not found else ", ".join(found), False)


def run_preflight(root: Path, *, product_version: str = "0.7.0") -> PreflightReport:
    """Run deterministic environment, source, offline, and licensing boundary checks."""

    checks = [python_version_check()]
    checks.extend(path_check(root, relative) for relative in REQUIRED_PROJECT_PATHS)
    checks.extend((
        writable_directory_check(root / "data"),
        offline_configuration_check(root),
        model_boundary_check(root),
        generated_artifact_check(root),
    ))
    return PreflightReport(tuple(checks), date.today().isoformat(), product_version)
