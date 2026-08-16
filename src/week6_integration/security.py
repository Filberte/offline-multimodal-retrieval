"""离线端点、允许路径和源代码泄漏检查。"""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from week6_integration.models import SecurityFinding, SecurityReview

_SOURCE_SUFFIXES = {".py", ".dart", ".yaml", ".yml", ".json", ".md", ".ps1", ".txt", ".toml", ".env", ".pem", ".key"}
_EXCLUDED_PARTS = {".dart_tool", ".git", "build", "coverage", "__pycache__"}


class SecurityPolicyError(ValueError):
    """表示请求违反本地数据安全边界。"""


class OfflineSecurityPolicy:
    """只允许本地路径和回环通信，并执行静态泄漏检查。"""

    def __init__(self, allowed_roots: Iterable[str | Path]) -> None:
        roots = tuple(Path(root).expanduser().resolve() for root in allowed_roots)
        if not roots:
            raise ValueError("at least one allowed root is required")
        self.allowed_roots = roots

    def validate_local_path(self, value: str | Path, *, must_exist: bool = True) -> Path:
        path = Path(value).expanduser().resolve(strict=False)
        if not any(path == root or path.is_relative_to(root) for root in self.allowed_roots):
            raise SecurityPolicyError(f"path is outside configured local roots: {path}")
        if must_exist and not path.exists():
            raise FileNotFoundError(path)
        return path

    @staticmethod
    def validate_endpoint(endpoint: str) -> str:
        """只接受回环 HTTP 端点；进程桥接不需要任何端点。"""

        parsed = urlparse(endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise SecurityPolicyError("endpoint must be an HTTP(S) loopback URL")
        host = parsed.hostname.casefold()
        if host == "localhost":
            return endpoint
        try:
            if ipaddress.ip_address(host).is_loopback:
                return endpoint
        except ValueError:
            pass
        raise SecurityPolicyError("external network endpoints are disabled")

    def scan_source_tree(self, roots: Iterable[str | Path]) -> SecurityReview:
        """扫描生产源码中的硬编码凭据和非回环 HTTP 端点。"""

        findings: list[SecurityFinding] = []
        scanned = 0
        for path in self._source_files(roots):
            scanned += 1
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                findings.append(
                    SecurityFinding(
                        "SEC-ENCODING",
                        "low",
                        str(path),
                        "源文件不是 UTF-8，无法完成文本泄漏检查。",
                    )
                )
                continue
            findings.extend(self._scan_text(path, text))
        return SecurityReview(scanned_files=scanned, findings=tuple(findings))

    @staticmethod
    def _source_files(roots: Iterable[str | Path]):
        seen: set[Path] = set()
        for raw_root in roots:
            root = Path(raw_root)
            candidates = (root,) if root.is_file() else root.rglob("*")
            for path in candidates:
                if (
                    path.is_file()
                    and path.suffix.casefold() in _SOURCE_SUFFIXES
                    and not any(part in _EXCLUDED_PARTS for part in path.parts)
                    and path not in seen
                ):
                    seen.add(path)
                    yield path

    @staticmethod
    def _scan_text(path: Path, text: str) -> list[SecurityFinding]:
        findings: list[SecurityFinding] = []
        aws_prefix = "AK" + "IA"
        aws_pattern = re.compile(rf"\b{aws_prefix}[0-9A-Z]{{16}}\b")
        private_key_marker = "-----BEGIN " + "PRIVATE KEY-----"
        if aws_pattern.search(text):
            findings.append(
                SecurityFinding("SEC-AWS-KEY", "critical", str(path), "发现疑似 AWS 访问密钥。")
            )
        if private_key_marker in text:
            findings.append(
                SecurityFinding("SEC-PRIVATE-KEY", "critical", str(path), "发现私钥正文。")
            )
        for match in re.finditer(r"https?://([^/\s'\"<>]+)", text, flags=re.IGNORECASE):
            host = match.group(1).split(":", 1)[0].strip("[]").casefold()
            if host == "localhost":
                continue
            try:
                if ipaddress.ip_address(host).is_loopback:
                    continue
            except ValueError:
                pass
            findings.append(
                SecurityFinding(
                    "SEC-EXTERNAL-ENDPOINT",
                    "high",
                    str(path),
                    f"发现非回环 HTTP 端点：{host}",
                )
            )
        return findings
