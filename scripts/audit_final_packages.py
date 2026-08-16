"""Validate final PDFs, archives, hashes, and Week 1–8 portfolio coverage."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "final_submit_7_files"
REPORTS = ROOT / "reports"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        corrupt = archive.testzip()
    return {
        "file": path.name,
        "entries": len(names),
        "corrupt_entry": corrupt,
        "names": names,
    }


def inspect_pdf(path: Path) -> dict:
    reader = PdfReader(str(path))
    lengths = [len((page.extract_text() or "").strip()) for page in reader.pages]
    return {
        "file": path.name,
        "pages": len(reader.pages),
        "text_lengths": lengths,
        "passed": len(reader.pages) > 0 and all(length >= 30 for length in lengths),
    }


def main() -> int:
    manifest = json.loads((REPORTS / "final_package_manifest.json").read_text(encoding="utf-8"))
    final_files = sorted(path for path in FINAL.iterdir() if path.is_file())
    actual_hashes = {path.name: sha256(path) for path in final_files}
    expected_hashes = {item["name"]: item["sha256"] for item in manifest["files"]}

    pdfs = [inspect_pdf(path) for path in final_files if path.suffix.casefold() == ".pdf"]
    zips = [inspect_zip(path) for path in final_files if path.suffix.casefold() == ".zip"]
    by_name = {item["file"]: item for item in zips}

    windows = by_name["02_Week8_Windows正式发布包_含600项测试.zip"]
    source = by_name["03_Week8_GitHub开源仓库就绪包.zip"]
    portfolio = by_name["05_Week8_完整实习作品集_Week1-8.zip"]

    windows_required = (
        "OfflineRetrieval_Windows_1.0.0/offline_retrieval_ui/offline_retrieval_ui.exe",
        "OfflineRetrieval_Windows_1.0.0/backend/offline_retrieval_backend.exe",
        "OfflineRetrieval_Windows_1.0.0/启动_离线多模态检索.cmd",
        "OfflineRetrieval_Windows_1.0.0/启动_完整模型演示_需项目环境.cmd",
        "OfflineRetrieval_Windows_1.0.0/demo_data/week1_final_demo/week1_demo_manifest.json",
    )
    source_required = (
        "offline-multimodal-retrieval/README.md",
        "offline-multimodal-retrieval/.github/workflows/cross-platform-release.yml",
        "offline-multimodal-retrieval/src/week8_delivery/readiness.py",
        "offline-multimodal-retrieval/tests/test_21_week8_readiness.py",
        "offline-multimodal-retrieval/reports/final_readiness.json",
    )
    portfolio_prefixes = tuple(
        f"Offline_Retrieval_Week1-8_Portfolio/Week{week}_" for week in range(1, 9)
    )

    checks = {
        "exactly_seven_final_files": len(final_files) == 7,
        "hashes_match_manifest": actual_hashes == expected_hashes,
        "all_pdfs_readable": len(pdfs) == 4 and all(item["passed"] for item in pdfs),
        "all_zips_integrity_ok": len(zips) == 3 and all(item["corrupt_entry"] is None for item in zips),
        "windows_required_entries": all(name in windows["names"] for name in windows_required),
        "source_required_entries": all(name in source["names"] for name in source_required),
        "source_has_no_ephemeral_or_build_cache": not any(
            "/ephemeral/" in name or "/.dart_tool/" in name or "/qa/" in name
            for name in source["names"]
        ),
        "portfolio_covers_week1_to_week8": all(
            any(name.startswith(prefix) for name in portfolio["names"])
            for prefix in portfolio_prefixes
        ),
        "portfolio_contains_project_brief": any("/00_Project_Brief/" in name for name in portfolio["names"]),
        "portfolio_contains_interview_kit": any("/Interview_Product_Manager_Kit/17_" in name for name in portfolio["names"]),
        "separate_interview_folder_has_18_markdown_files": len(list((ROOT / "Interview_Product_Manager_Kit").glob("*.md"))) == 18,
    }
    report = {
        "checks": checks,
        "passed": all(checks.values()),
        "pdfs": pdfs,
        "archives": [
            {key: value for key, value in item.items() if key != "names"}
            for item in zips
        ],
        "actual_hashes": actual_hashes,
    }
    (REPORTS / "final_package_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
