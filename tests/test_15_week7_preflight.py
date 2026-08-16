"""Week 7 安装、离线边界与包洁净度预检测试，共 35 项。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from week7_release.models import PreflightCheck, PreflightReport
from week7_release.preflight import (
    REQUIRED_PROJECT_PATHS,
    generated_artifact_check,
    model_boundary_check,
    offline_configuration_check,
    path_check,
    python_version_check,
    run_preflight,
    writable_directory_check,
)


class Week7PreflightTests(unittest.TestCase):
    def test_336_python_312_passes(self):
        self.assertTrue(python_version_check((3, 12, 0)).passed)

    def test_337_python_311_fails(self):
        self.assertTrue(python_version_check((3, 11, 9)).blocking)

    def test_338_future_python_version_passes(self):
        self.assertEqual(python_version_check((4, 0, 0)).status, "pass")

    def test_339_preflight_check_rejects_unknown_status(self):
        with self.assertRaisesRegex(ValueError, "status"):
            PreflightCheck("X", "x", "unknown", "x")

    def test_340_pass_check_is_not_blocking(self):
        check = PreflightCheck("X", "x", "pass", "ok")
        self.assertEqual((check.passed, check.blocking), (True, False))

    def test_341_required_fail_is_blocking(self):
        self.assertTrue(PreflightCheck("X", "x", "fail", "bad", True).blocking)

    def test_342_optional_fail_is_not_blocking(self):
        self.assertFalse(PreflightCheck("X", "x", "fail", "bad", False).blocking)

    def test_343_check_serialization_includes_blocking(self):
        self.assertIn("blocking", PreflightCheck("X", "x", "warn", "note").to_dict())

    def test_344_empty_preflight_is_not_release_ready(self):
        self.assertFalse(PreflightReport((), "2026-08-13", "0.7.0").release_ready)

    def test_345_all_passing_checks_are_release_ready(self):
        report = PreflightReport((PreflightCheck("X", "x", "pass", "ok"),), "2026-08-13", "0.7.0")
        self.assertTrue(report.release_ready)

    def test_346_report_counts_blocking_failures(self):
        report = PreflightReport((PreflightCheck("X", "x", "fail", "bad"),), "2026-08-13", "0.7.0")
        self.assertEqual(report.failed, 1)

    def test_347_report_counts_warnings(self):
        report = PreflightReport((PreflightCheck("X", "x", "warn", "note", False),), "2026-08-13", "0.7.0")
        self.assertEqual(report.warnings, 1)

    def test_348_report_serializes_product_version(self):
        report = PreflightReport((PreflightCheck("X", "x", "pass", "ok"),), "2026-08-13", "0.7.0")
        self.assertEqual(report.to_dict()["product_version"], "0.7.0")

    def test_349_existing_required_path_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "file").touch()
            self.assertTrue(path_check(Path(directory), "file").passed)

    def test_350_missing_required_path_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(path_check(Path(directory), "missing").status, "fail")

    def test_351_missing_optional_path_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(path_check(Path(directory), "missing", required=False).status, "warn")

    def test_352_writable_directory_probe_cleans_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "data"
            self.assertTrue(writable_directory_check(target).passed)
            self.assertEqual(list(target.iterdir()), [])

    def test_353_offline_check_passes_without_source_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(offline_configuration_check(Path(directory)).passed)

    def test_354_offline_check_accepts_https_client_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "src/client.py"
            path.parent.mkdir()
            path.write_text("url = 'https://docs.example.test'", encoding="utf-8")
            self.assertTrue(offline_configuration_check(Path(directory)).passed)

    def test_355_offline_check_rejects_http_server_import(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "src/server.py"
            path.parent.mkdir()
            path.write_text("import http.server", encoding="utf-8")
            self.assertTrue(offline_configuration_check(Path(directory)).blocking)

    def test_356_offline_check_rejects_listener_call(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "src/server.py"
            path.parent.mkdir()
            path.write_text("socket.listen(5)", encoding="utf-8")
            self.assertEqual(offline_configuration_check(Path(directory)).status, "fail")

    def test_357_offline_check_rejects_wildcard_bind_address(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "src/server.py"
            path.parent.mkdir()
            path.write_text("host = '0.0.0.0'", encoding="utf-8")
            self.assertIn("server.py", offline_configuration_check(Path(directory)).detail)

    def test_358_model_boundary_passes_without_weights(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(model_boundary_check(Path(directory)).passed)

    def test_359_model_boundary_rejects_pt(self):
        self._assert_model_extension_fails(".pt")

    def test_360_model_boundary_rejects_pth(self):
        self._assert_model_extension_fails(".pth")

    def test_361_model_boundary_rejects_ckpt(self):
        self._assert_model_extension_fails(".ckpt")

    def test_362_model_boundary_rejects_onnx(self):
        self._assert_model_extension_fails(".onnx")

    def test_363_model_boundary_rejects_tflite(self):
        self._assert_model_extension_fails(".tflite")

    def test_364_model_boundary_rejects_safetensors(self):
        self._assert_model_extension_fails(".safetensors")

    def test_365_clean_source_has_passing_artifact_check(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(generated_artifact_check(Path(directory)).passed)

    def test_366_generated_cache_creates_nonblocking_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "__pycache__").mkdir()
            check = generated_artifact_check(Path(directory))
            self.assertEqual((check.status, check.blocking), ("warn", False))

    def test_367_required_project_contract_has_eight_paths(self):
        self.assertEqual(len(REQUIRED_PROJECT_PATHS), 8)

    def test_368_preflight_on_empty_root_reports_missing_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run_preflight(Path(directory))
            self.assertGreaterEqual(report.failed, len(REQUIRED_PROJECT_PATHS))

    def test_369_preflight_reports_requested_product_version(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run_preflight(Path(directory), product_version="9.9.9")
            self.assertEqual(report.product_version, "9.9.9")

    def test_370_preflight_current_release_root_has_no_blocking_failure(self):
        root = Path(__file__).resolve().parents[1]
        report = run_preflight(root)
        self.assertTrue(report.release_ready, report.to_dict())

    def _assert_model_extension_fails(self, extension: str):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / f"model{extension}").touch()
            self.assertTrue(model_boundary_check(Path(directory)).blocking)


if __name__ == "__main__":
    unittest.main()
