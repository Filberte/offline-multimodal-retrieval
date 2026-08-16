"""Cross-platform evidence boundary tests, TC-551 through TC-575."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from week8_delivery.models import PlatformAssessment, PlatformCheck
from week8_delivery.platforms import evaluate_platforms


def _platform_root(root: Path, *, windows: bool = True, workflow: bool = True) -> None:
    app = root / "app/offline_retrieval_ui"
    for folder in ("macos", "linux"):
        (app / folder).mkdir(parents=True, exist_ok=True)
    for path in (app / "lib/main.dart", app / "pubspec.yaml"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok", encoding="utf-8")
    for name in ("week2_parser", "week3_embedding", "week4_retrieval", "week6_integration", "week7_release", "week8_delivery"):
        (root / "src" / name).mkdir(parents=True, exist_ok=True)
    if workflow:
        path = root / ".github/workflows/cross-platform-release.yml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("workflow", encoding="utf-8")
    if windows:
        release = root / "release/windows/offline_retrieval_ui"
        (release / "data").mkdir(parents=True, exist_ok=True)
        (release / "offline_retrieval_ui.exe").write_bytes(b"exe")
        (release / "flutter_windows.dll").write_bytes(b"dll")
        launcher = root / "release/windows/启动_离线多模态检索.cmd"
        launcher.parent.mkdir(parents=True, exist_ok=True)
        launcher.write_text("start", encoding="utf-8")


class Week8PlatformTests(unittest.TestCase):
    def test_551_platform_check_pass_property(self):
        self.assertTrue(PlatformCheck("x", "p", "l", "pass", "e").passed)

    def test_552_platform_check_fail_property(self):
        self.assertFalse(PlatformCheck("x", "p", "l", "fail", "e").passed)

    def test_553_platform_check_serializes_passed(self):
        self.assertTrue(PlatformCheck("x", "p", "l", "pass", "e").to_dict()["passed"])

    def test_554_platform_assessment_detects_blocking_failure(self):
        check = PlatformCheck("x", "p", "l", "fail", "e")
        self.assertEqual(len(PlatformAssessment("p", "e", (check,), "NO-GO").blocking_failures), 1)

    def test_555_nonblocking_failure_is_not_blocker(self):
        check = PlatformCheck("x", "p", "l", "fail", "e", False)
        self.assertFalse(PlatformAssessment("p", "e", (check,), "GO").blocking_failures)

    def test_556_evaluate_returns_three_platforms(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertEqual(len(evaluate_platforms(temp)), 3)

    def test_557_platform_order_is_windows_macos_linux(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertEqual([x.platform for x in evaluate_platforms(temp)], ["Windows", "macOS", "Linux"])

    def test_558_windows_uses_real_evidence_class(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertIn("real_host", evaluate_platforms(temp)[0].evidence_class)

    def test_559_windows_go_with_complete_release(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertEqual(evaluate_platforms(temp)[0].decision, "GO")

    def test_560_windows_no_go_without_executable(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp), windows=False); self.assertEqual(evaluate_platforms(temp)[0].decision, "NO-GO")

    def test_561_windows_no_go_on_non_windows_host(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Linux"):
            _platform_root(Path(temp)); self.assertEqual(evaluate_platforms(temp)[0].decision, "NO-GO")

    def test_562_windows_checks_executable(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertTrue(any(x.code == "WIN-002" and x.passed for x in evaluate_platforms(temp)[0].checks))

    def test_563_windows_checks_runtime_dll(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertTrue(any(x.code == "WIN-003" and x.passed for x in evaluate_platforms(temp)[0].checks))

    def test_564_windows_checks_data_directory(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertTrue(any(x.code == "WIN-004" and x.passed for x in evaluate_platforms(temp)[0].checks))

    def test_565_windows_checks_launcher(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertTrue(any(x.code == "WIN-005" and x.passed for x in evaluate_platforms(temp)[0].checks))

    def test_566_macos_is_simulation(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertIn("simulation", evaluate_platforms(temp)[1].evidence_class)

    def test_567_linux_is_simulation(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertIn("simulation", evaluate_platforms(temp)[2].evidence_class)

    def test_568_macos_decision_requires_real_execution(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertIn("REAL_MACOS_EXECUTION_PENDING", evaluate_platforms(temp)[1].decision)

    def test_569_linux_decision_requires_real_execution(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertIn("REAL_LINUX_EXECUTION_PENDING", evaluate_platforms(temp)[2].decision)

    def test_570_macos_limitations_name_xcode(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertIn("Xcode", " ".join(evaluate_platforms(temp)[1].limitations))

    def test_571_macos_limitations_name_voiceover(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp)); self.assertIn("VoiceOver", " ".join(evaluate_platforms(temp)[1].limitations))

    def test_572_missing_workflow_blocks_simulations(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            _platform_root(Path(temp), workflow=False); self.assertTrue(evaluate_platforms(temp)[1].blocking_failures)

    def test_573_missing_source_package_blocks_macos(self):
        with tempfile.TemporaryDirectory() as temp, patch("platform.system", return_value="Windows"):
            root = Path(temp); _platform_root(root); (root / "src/week3_embedding").rmdir(); self.assertTrue(evaluate_platforms(root)[1].blocking_failures)

    def test_574_assessment_serializes_limitations(self):
        self.assertEqual(PlatformAssessment("p", "sim", (), "pending", ("limit",)).to_dict()["limitations"], ["limit"])

    def test_575_assessment_serializes_blocking_count(self):
        check = PlatformCheck("x", "p", "l", "fail", "e")
        self.assertEqual(PlatformAssessment("p", "sim", (check,), "blocked").to_dict()["blocking_failures"], 1)
