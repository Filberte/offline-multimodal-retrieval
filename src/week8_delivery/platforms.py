"""Truthful platform evidence classification for the Week 8 hand-off."""

from __future__ import annotations

import platform
from pathlib import Path

from week8_delivery.models import PlatformAssessment, PlatformCheck


def _check(code: str, target: str, label: str, condition: bool, evidence: str, *, blocking: bool = True) -> PlatformCheck:
    return PlatformCheck(code, target, label, "pass" if condition else "fail", evidence, blocking)


def _source_checks(root: Path, platform_name: str, folder: str, prefix: str) -> tuple[PlatformCheck, ...]:
    app = root / "app" / "offline_retrieval_ui"
    target = app / folder
    return (
        _check(f"{prefix}-001", platform_name, "Flutter target directory", target.is_dir(), str(target)),
        _check(f"{prefix}-002", platform_name, "Flutter project metadata", (app / "pubspec.yaml").is_file(), "pubspec.yaml present"),
        _check(f"{prefix}-003", platform_name, "Shared Dart application", (app / "lib" / "main.dart").is_file(), "lib/main.dart present"),
        _check(f"{prefix}-004", platform_name, "Self-contained Python sources", all((root / "src" / name).is_dir() for name in ("week2_parser", "week3_embedding", "week4_retrieval", "week6_integration", "week7_release", "week8_delivery")), "Week 2/3/4/6/7/8 packages present"),
        _check(f"{prefix}-005", platform_name, "Cross-platform CI job", (root / ".github" / "workflows" / "cross-platform-release.yml").is_file(), "GitHub Actions workflow present"),
    )


def evaluate_platforms(root: str | Path) -> tuple[PlatformAssessment, ...]:
    base = Path(root).resolve()
    windows_release = base / "release" / "windows" / "offline_retrieval_ui"
    windows_checks = (
        _check("WIN-001", "Windows", "Host operating system", platform.system() == "Windows", platform.platform()),
        _check("WIN-002", "Windows", "Flutter release executable", (windows_release / "offline_retrieval_ui.exe").is_file(), str(windows_release / "offline_retrieval_ui.exe")),
        _check("WIN-003", "Windows", "Flutter runtime DLL", (windows_release / "flutter_windows.dll").is_file(), str(windows_release / "flutter_windows.dll")),
        _check("WIN-004", "Windows", "Release asset directory", (windows_release / "data").is_dir(), str(windows_release / "data")),
        _check("WIN-005", "Windows", "One-click launcher", (base / "release" / "windows" / "启动_离线多模态检索.cmd").is_file(), "Windows launcher present"),
    )
    windows = PlatformAssessment("Windows", "real_host_build_and_execution", windows_checks, "GO" if all(c.passed for c in windows_checks) else "NO-GO")

    mac_checks = _source_checks(base, "macOS", "macos", "MAC-SIM")
    mac = PlatformAssessment(
        "macOS",
        "windows_hosted_source_and_contract_simulation",
        mac_checks,
        "SOURCE_COMPATIBLE_REAL_MACOS_EXECUTION_PENDING" if all(c.passed for c in mac_checks) else "SOURCE_COMPATIBILITY_BLOCKED",
        (
            "未在 Apple 硬件/Xcode 上构建或启动。",
            "未执行 codesign、notarization、Gatekeeper 或 VoiceOver 实机验证。",
        ),
    )
    linux_checks = _source_checks(base, "Linux", "linux", "LINUX-SIM")
    linux = PlatformAssessment(
        "Linux",
        "windows_hosted_source_and_contract_simulation",
        linux_checks,
        "SOURCE_COMPATIBLE_REAL_LINUX_EXECUTION_PENDING" if all(c.passed for c in linux_checks) else "SOURCE_COMPATIBILITY_BLOCKED",
        ("未在 Linux 主机上执行 flutter build linux 或启动验证。",),
    )
    return windows, mac, linux
