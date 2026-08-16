"""Week 6 本地安全策略与进程桥接测试，共 30 项。"""

from __future__ import annotations

import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from week4_retrieval.models import IndexingSummary, SearchResponse
from week6_integration.bridge import BridgeApplication, serve_stdio
from week6_integration.factory import _build_offline_vector_store
from week6_integration.models import BackendHealth, CacheStats, RuntimeMetrics
from week6_integration.security import OfflineSecurityPolicy, SecurityPolicyError


def make_health() -> BackendHealth:
    cache = CacheStats(0, 0, 0, 0, 8)
    metrics = RuntimeMetrics(0, 0, 0, 0, 0, 0, 0.0)
    return BackendHealth(
        status="ready",
        mode="integrated-local",
        offline_only=True,
        backend_name="test-backend",
        vector_store="memory",
        indexed_records=0,
        uptime_seconds=1.0,
        embedding_cache=cache,
        query_cache=cache,
        metrics=metrics,
    )


class FakeBridgeService:
    def __init__(self):
        self.last_query = None
        self.last_paths = None
        self.last_directory = None

    def health(self):
        return make_health()

    def library_items(self):
        return ({"item_id": "a", "file_name": "a.txt"},)

    def search(self, request):
        request.validate()
        self.last_query = request
        return SearchResponse(request.text, (), 0.5, 0)

    def index_paths(self, paths, *, continue_on_error=True):
        self.last_paths = tuple(paths)
        return IndexingSummary(len(self.last_paths), len(self.last_paths), (), len(self.last_paths), (), len(self.last_paths))

    def index_directory(self, root, *, recursive=True, continue_on_error=True):
        self.last_directory = (Path(root), recursive)
        return IndexingSummary(1, 1, (), 1, (), 1)


class SecurityBridgeTests(unittest.TestCase):
    def test_211_policy_requires_allowed_root(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            OfflineSecurityPolicy([])

    def test_212_policy_accepts_configured_root(self):
        with tempfile.TemporaryDirectory() as temp:
            policy = OfflineSecurityPolicy([temp])
            self.assertEqual(policy.validate_local_path(temp), Path(temp).resolve())

    def test_213_policy_accepts_child_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "a.txt"
            path.write_text("alpha", encoding="utf-8")
            policy = OfflineSecurityPolicy([temp])
            self.assertEqual(policy.validate_local_path(path), path.resolve())

    def test_214_policy_rejects_path_outside_root(self):
        with tempfile.TemporaryDirectory() as temp:
            policy = OfflineSecurityPolicy([temp])
            outside = Path(temp).parent / "week6-outside-214.txt"
            with self.assertRaises(SecurityPolicyError):
                policy.validate_local_path(outside, must_exist=False)

    def test_215_policy_rejects_missing_child_by_default(self):
        with tempfile.TemporaryDirectory() as temp:
            policy = OfflineSecurityPolicy([temp])
            with self.assertRaises(FileNotFoundError):
                policy.validate_local_path(Path(temp) / "missing.txt")

    def test_216_policy_can_validate_future_child_path(self):
        with tempfile.TemporaryDirectory() as temp:
            policy = OfflineSecurityPolicy([temp])
            result = policy.validate_local_path(
                Path(temp) / "future.txt",
                must_exist=False,
            )
            self.assertEqual(result.name, "future.txt")

    def test_217_policy_accepts_localhost_endpoint(self):
        endpoint = "http://localhost:8123/health"
        self.assertEqual(OfflineSecurityPolicy.validate_endpoint(endpoint), endpoint)

    def test_218_policy_accepts_ipv4_loopback_endpoint(self):
        endpoint = "http://127.0.0.1:8123"
        self.assertEqual(OfflineSecurityPolicy.validate_endpoint(endpoint), endpoint)

    def test_219_policy_accepts_ipv6_loopback_endpoint(self):
        endpoint = "http://[::1]:8123"
        self.assertEqual(OfflineSecurityPolicy.validate_endpoint(endpoint), endpoint)

    def test_220_policy_rejects_external_endpoint(self):
        with self.assertRaisesRegex(SecurityPolicyError, "external"):
            OfflineSecurityPolicy.validate_endpoint("https://example.com/api")

    def test_221_policy_rejects_non_http_endpoint(self):
        with self.assertRaises(SecurityPolicyError):
            OfflineSecurityPolicy.validate_endpoint("file:///tmp/data")

    @patch("chromadb.PersistentClient")
    def test_222_chroma_factory_disables_anonymized_telemetry(self, persistent_client):
        with tempfile.TemporaryDirectory() as temp:
            store = _build_offline_vector_store(Path(temp), {"test-space": 2})
        settings = persistent_client.call_args.kwargs["settings"]
        self.assertFalse(settings.anonymized_telemetry)
        self.assertIs(store._client, persistent_client.return_value)

    def test_223_scan_clean_source_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "clean.py"
            path.write_text("value = 1\n", encoding="utf-8")
            review = OfflineSecurityPolicy([temp]).scan_source_tree([temp])
        self.assertEqual((review.scanned_files, review.passed), (1, True))

    def test_224_scan_detects_aws_access_key(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "secret.py"
            path.write_text("key = 'AKIA1234567890ABCDEF'\n", encoding="utf-8")
            review = OfflineSecurityPolicy([temp]).scan_source_tree([temp])
        self.assertEqual(review.findings[0].code, "SEC-AWS-KEY")

    def test_225_scan_detects_private_key_marker(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "secret.txt"
            path.write_text("-----BEGIN PRIVATE KEY-----\n", encoding="utf-8")
            review = OfflineSecurityPolicy([temp]).scan_source_tree([temp])
        self.assertEqual(review.findings[0].code, "SEC-PRIVATE-KEY")

    def test_226_scan_detects_external_http_endpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "client.dart"
            path.write_text("const url = 'https://service.example/api';\n", encoding="utf-8")
            review = OfflineSecurityPolicy([temp]).scan_source_tree([temp])
        self.assertEqual(review.findings[0].severity, "high")

    def test_227_scan_ignores_localhost_endpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "client.dart"
            path.write_text("const url = 'http://localhost:8080';\n", encoding="utf-8")
            review = OfflineSecurityPolicy([temp]).scan_source_tree([temp])
        self.assertTrue(review.passed)

    def test_228_scan_ignores_numeric_loopback_endpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "client.py"
            path.write_text("url = 'http://127.0.0.1:8080'\n", encoding="utf-8")
            review = OfflineSecurityPolicy([temp]).scan_source_tree([temp])
        self.assertEqual(review.findings, ())

    def test_229_scan_excludes_build_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            build = Path(temp) / "build"
            build.mkdir()
            (build / "generated.py").write_text(
                "url = 'https://external.example'\n",
                encoding="utf-8",
            )
            review = OfflineSecurityPolicy([temp]).scan_source_tree([temp])
        self.assertEqual(review.scanned_files, 0)

    def test_230_scan_ignores_binary_suffix(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "payload.bin"
            path.write_bytes(b"https://external.example")
            review = OfflineSecurityPolicy([temp]).scan_source_tree([temp])
        self.assertEqual(review.scanned_files, 0)

    def test_231_review_counts_critical_findings(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "secret.py"
            path.write_text("key='AKIA1234567890ABCDEF'", encoding="utf-8")
            review = OfflineSecurityPolicy([temp]).scan_source_tree([temp])
        self.assertEqual(review.critical_findings, 1)

    def test_232_review_with_high_finding_does_not_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "client.py"
            path.write_text("url='https://external.example'", encoding="utf-8")
            review = OfflineSecurityPolicy([temp]).scan_source_tree([temp])
        self.assertEqual((review.high_findings, review.passed), (1, False))

    def test_233_bridge_ping_echoes_request_id(self):
        with tempfile.TemporaryDirectory() as temp:
            app = BridgeApplication(FakeBridgeService(), OfflineSecurityPolicy([temp]))
            response = app.handle({"request_id": "233", "command": "ping"})
        self.assertEqual((response["request_id"], response["data"]["message"]), ("233", "pong"))

    def test_234_bridge_health_serializes_backend(self):
        with tempfile.TemporaryDirectory() as temp:
            app = BridgeApplication(FakeBridgeService(), OfflineSecurityPolicy([temp]))
            response = app.handle({"command": "health"})
        self.assertEqual(response["data"]["status"], "ready")

    def test_235_bridge_library_returns_items(self):
        with tempfile.TemporaryDirectory() as temp:
            app = BridgeApplication(FakeBridgeService(), OfflineSecurityPolicy([temp]))
            response = app.handle({"command": "library"})
        self.assertEqual(response["data"]["items"][0]["file_name"], "a.txt")

    def test_236_bridge_maps_search_query_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            service = FakeBridgeService()
            app = BridgeApplication(service, OfflineSecurityPolicy([temp]))
            response = app.handle(
                {
                    "command": "search",
                    "data": {
                        "query": "alpha",
                        "top_k": 4,
                        "extension": "txt",
                        "include_images": False,
                    },
                }
            )
        self.assertTrue(response["ok"])
        self.assertEqual(
            (service.last_query.top_k, service.last_query.filters.extension),
            (4, "txt"),
        )

    def test_237_bridge_rejects_missing_command(self):
        with tempfile.TemporaryDirectory() as temp:
            app = BridgeApplication(FakeBridgeService(), OfflineSecurityPolicy([temp]))
            response = app.handle({"request_id": "237"})
        self.assertEqual(response["error"]["code"], "invalid_request")

    def test_238_bridge_rejects_unknown_command(self):
        with tempfile.TemporaryDirectory() as temp:
            app = BridgeApplication(FakeBridgeService(), OfflineSecurityPolicy([temp]))
            response = app.handle({"command": "unknown"})
        self.assertFalse(response["ok"])

    def test_239_bridge_indexes_valid_local_path(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "a.txt"
            path.write_text("alpha", encoding="utf-8")
            service = FakeBridgeService()
            app = BridgeApplication(service, OfflineSecurityPolicy([temp]))
            response = app.handle(
                {"command": "index_paths", "data": {"paths": [str(path)]}}
            )
        self.assertEqual(response["data"]["persisted_vectors"], 1)
        self.assertEqual(service.last_paths[0].name, "a.txt")

    def test_240_stdio_reports_invalid_json_then_shutdown(self):
        with tempfile.TemporaryDirectory() as temp:
            app = BridgeApplication(FakeBridgeService(), OfflineSecurityPolicy([temp]))
            input_stream = StringIO(
                "not-json\n"
                + json.dumps({"request_id": "240", "command": "shutdown"})
                + "\n"
            )
            output_stream = StringIO()
            exit_code = serve_stdio(
                app,
                input_stream=input_stream,
                output_stream=output_stream,
            )
        responses = [
            json.loads(line) for line in output_stream.getvalue().splitlines()
        ]
        self.assertEqual((exit_code, responses[0]["error"]["code"]), (0, "invalid_json"))
        self.assertTrue(responses[1]["ok"])


if __name__ == "__main__":
    unittest.main()
