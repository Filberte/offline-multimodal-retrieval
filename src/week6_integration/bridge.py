"""Flutter 与 Python 核心之间的本地标准输入输出协议。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

from week4_retrieval.models import SearchFilters, SearchQuery
from week6_integration.security import OfflineSecurityPolicy, SecurityPolicyError
from week6_integration.service import IntegratedRetrievalService


class BridgeApplication:
    """处理单条 JSON 请求，不监听网络端口。"""

    def __init__(
        self,
        service: IntegratedRetrievalService,
        policy: OfflineSecurityPolicy,
    ) -> None:
        self.service = service
        self.policy = policy
        self.shutdown_requested = False

    def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        request_id = str(payload.get("request_id", ""))
        try:
            command = str(payload.get("command", "")).strip()
            if not command:
                raise ValueError("command is required")
            data = self._dispatch(command, payload.get("data"))
            return {"ok": True, "request_id": request_id, "data": data}
        except (FileNotFoundError, SecurityPolicyError, TypeError, ValueError) as exc:
            return self._error(request_id, "invalid_request", str(exc))
        except Exception as exc:
            return self._error(request_id, "backend_error", str(exc))

    def _dispatch(self, command: str, data: Any) -> Any:
        values = data if isinstance(data, dict) else {}
        if command == "ping":
            return {"message": "pong", "offline_only": True}
        if command == "health":
            return self.service.health().to_dict()
        if command == "library":
            return {"items": list(self.service.library_items())}
        if command == "search":
            request = self._search_query(values)
            return self.service.search(request).to_dict()
        if command == "index_paths":
            raw_paths = values.get("paths")
            if not isinstance(raw_paths, list) or not raw_paths:
                raise ValueError("paths must be a non-empty list")
            paths = [self.policy.validate_local_path(str(path)) for path in raw_paths]
            summary = self.service.index_paths(
                paths,
                continue_on_error=bool(values.get("continue_on_error", True)),
            )
            return {
                "discovered_files": summary.discovered_files,
                "parsed_files": summary.parsed_files,
                "parse_failures": list(summary.parse_failures),
                "embedding_inputs": summary.embedding_inputs,
                "embedding_failures": list(summary.embedding_failures),
                "persisted_vectors": summary.persisted_vectors,
                "success": summary.success,
            }
        if command == "index_directory":
            root = self.policy.validate_local_path(str(values.get("path", "")))
            summary = self.service.index_directory(
                root,
                recursive=bool(values.get("recursive", True)),
                continue_on_error=bool(values.get("continue_on_error", True)),
            )
            return {
                "discovered_files": summary.discovered_files,
                "parsed_files": summary.parsed_files,
                "parse_failures": list(summary.parse_failures),
                "embedding_inputs": summary.embedding_inputs,
                "embedding_failures": list(summary.embedding_failures),
                "persisted_vectors": summary.persisted_vectors,
                "success": summary.success,
            }
        if command == "shutdown":
            self.shutdown_requested = True
            return {"message": "shutdown acknowledged"}
        raise ValueError(f"unsupported command: {command}")

    @staticmethod
    def _search_query(values: dict[str, Any]) -> SearchQuery:
        filters = SearchFilters(
            modality=BridgeApplication._optional_string(values.get("modality")),
            content_type=BridgeApplication._optional_string(values.get("content_type")),
            extension=BridgeApplication._optional_string(values.get("extension")),
            document_id=BridgeApplication._optional_string(values.get("document_id")),
            source_path_contains=BridgeApplication._optional_string(
                values.get("source_path")
            ),
        )
        return SearchQuery(
            text=str(values.get("query", "")),
            top_k=int(values.get("top_k", 10)),
            semantic_weight=float(values.get("semantic_weight", 0.7)),
            keyword_weight=float(values.get("keyword_weight", 0.3)),
            include_cross_modal=bool(values.get("include_images", True)),
            filters=filters,
        )

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _error(request_id: str, code: str, message: str) -> dict[str, Any]:
        return {
            "ok": False,
            "request_id": request_id,
            "error": {"code": code, "message": message},
        }


def serve_stdio(
    application: BridgeApplication,
    *,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> int:
    """逐行读取请求并立即刷新响应，供 Flutter 子进程调用。"""

    for raw_line in input_stream:
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise TypeError("request must be a JSON object")
            response = application.handle(payload)
        except (json.JSONDecodeError, TypeError) as exc:
            response = BridgeApplication._error("", "invalid_json", str(exc))
        output_stream.write(json.dumps(response, ensure_ascii=False) + "\n")
        output_stream.flush()
        if application.shutdown_requested:
            break
    return 0
