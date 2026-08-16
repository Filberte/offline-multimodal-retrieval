"""Build the clean source, Windows release, and Week 1–8 portfolio archives."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
MANAGER = ROOT / "manager_submission"
FINAL = ROOT / "final_submit_7_files"
PORTFOLIO = ROOT / "portfolio"
SUBMISSION_DATE = "2026-08-20"

WINDOWS_ZIP = MANAGER / "02_Week8_Windows正式发布包_含600项测试.zip"
SOURCE_ZIP = MANAGER / "03_Week8_GitHub开源仓库就绪包.zip"
PORTFOLIO_ZIP = MANAGER / "05_Week8_完整实习作品集_Week1-8.zip"


def _safe_reset(path: Path) -> None:
    resolved = path.resolve()
    if resolved.parent != ROOT.resolve() or resolved.name not in {"portfolio", "final_submit_7_files"}:
        raise RuntimeError(f"Refusing to reset unexpected path: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)


def _ignored(relative: Path) -> bool:
    parts = {part.casefold() for part in relative.parts}
    if parts & {"__pycache__", ".dart_tool", ".idea", ".symlinks", "ephemeral", "build", "coverage", "dist", "dist_slim", "build_slim", "qa", "data", "release", "portfolio", "manager_submission", "final_submit_7_files"}:
        return True
    if relative.suffix.casefold() in {".pyc", ".pyo", ".zip"}:
        return True
    return False


def _write_tree(zip_file: zipfile.ZipFile, source: Path, archive_root: Path, *, filter_source: bool = False) -> None:
    if source.is_file():
        zip_file.write(source, (archive_root / source.name).as_posix())
        return
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        if filter_source and _ignored(relative):
            continue
        zip_file.write(path, (archive_root / relative).as_posix())


def build_source_zip() -> None:
    top_files = [
        ".gitignore", "README.md", "CHANGELOG.md", "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md", "SECURITY.md", "LICENSE", "NOTICE",
        "THIRD_PARTY_NOTICES.md", "MODEL_AND_DATA_LICENSES.md",
        "REPOSITORY_PUBLISH_CHECKLIST.md", "pyproject.toml", "run_backend.py",
        "run_core_tests.py", "run_tests.py", "offline_retrieval_backend.spec",
    ]
    trees = [".github", "src", "tests", "scripts", "docs", "demo_data", "app"]
    with zipfile.ZipFile(SOURCE_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        base = Path("offline-multimodal-retrieval")
        for name in top_files:
            path = ROOT / name
            if path.is_file():
                archive.write(path, (base / name).as_posix())
        for name in trees:
            path = ROOT / name
            if path.exists():
                _write_tree(archive, path, base / name, filter_source=True)
        for name in (
            "combined_test_summary.json", "coverage_summary.json", "test_case_catalog.json",
            "week1_demo_validation.json", "production_model_demo_smoke.json",
            "platform_evidence.json", "week1_to_week8_lineage.json", "final_readiness.json",
        ):
            path = ROOT / "reports" / name
            if path.is_file():
                archive.write(path, (base / "reports" / name).as_posix())


def build_windows_zip() -> None:
    with zipfile.ZipFile(WINDOWS_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=7) as archive:
        base = Path("OfflineRetrieval_Windows_1.0.0")
        _write_tree(archive, ROOT / "release" / "windows", base)
        _write_tree(archive, ROOT / "demo_data" / "week1_final_demo", base / "demo_data" / "week1_final_demo")
        for name in ("combined_test_summary.json", "production_model_demo_smoke.json", "platform_evidence.json"):
            path = ROOT / "reports" / name
            archive.write(path, (base / "reports" / name).as_posix())


def _copy_directory_files(
    source: Path,
    target: Path,
    suffixes: set[str] | None = None,
    exclude_names: set[str] | None = None,
) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.iterdir()):
        if not path.is_file():
            continue
        if suffixes is not None and path.suffix.casefold() not in suffixes:
            continue
        if exclude_names and path.name in exclude_names:
            continue
        shutil.copy2(path, target / path.name)


def build_portfolio() -> None:
    _safe_reset(PORTFOLIO)
    overview = """# Offline Accessible Multimodal Local Content Retrieval — Week 1–8 Portfolio

This portfolio preserves the signed-off contribution of every week. Week 8 does not replace earlier work: it integrates, verifies, packages, and explains it.

- Week 1: requirements, environment, curated datasets, and risk baseline.
- Week 2: architecture and multi-format parser.
- Week 3: local text/image embedding.
- Week 4: Chroma, BM25, hybrid retrieval, and E2E relevance.
- Week 5: Flutter UI and accessibility engineering.
- Week 6: integration, performance, defects, security, and 300-test baseline.
- Week 7: maintenance/API/user documentation, OSS compliance, release governance, and 500 tests.
- Week 8: Windows production baseline, Week 1 demo, 600 tests, platform evidence, final reports, and interview handoff.

Evidence boundary: Windows has real-host build/execution evidence. macOS/Linux remain source-contract simulations until native artifacts are attached.
"""
    (PORTFOLIO / "00_作品集总览.md").write_text(overview, encoding="utf-8")

    brief = PROJECT / "Software Engineering Project Offline Accessible Multimodal Local Content Retrieval System.pdf"
    if brief.is_file():
        target = PORTFOLIO / "00_Project_Brief"
        target.mkdir()
        shutil.copy2(brief, target / brief.name)

    _copy_directory_files(PROJECT / "Week1_Deliverables", PORTFOLIO / "Week1_Requirements_Data_Risk", {".docx", ".pdf", ".md"})
    _copy_directory_files(PROJECT / "Week2_Deliverables" / "manager_submission", PORTFOLIO / "Week2_Architecture_Parser")
    _copy_directory_files(PROJECT / "Week3_Deliverables" / "manager_submission", PORTFOLIO / "Week3_Embedding")
    _copy_directory_files(PROJECT / "Week4_Deliverables" / "manager_submission", PORTFOLIO / "Week4_Retrieval")
    _copy_directory_files(PROJECT / "Week5_Deliverables" / "final_submission", PORTFOLIO / "Week5_UI_Accessibility")
    _copy_directory_files(PROJECT / "Week6_Deliverables" / "final_submit_7_files", PORTFOLIO / "Week6_Integration_Quality")
    _copy_directory_files(PROJECT / "Week7_Deliverables" / "final_submit_7_files", PORTFOLIO / "Week7_Documentation_Release")

    week8 = PORTFOLIO / "Week8_Final_Delivery"
    _copy_directory_files(MANAGER, week8, {".pdf", ".docx"})
    _copy_directory_files(
        ROOT / "reports",
        week8 / "Machine_Readable_Evidence",
        {".json", ".txt"},
        {"final_package_manifest.json", "final_package_audit.json"},
    )
    shutil.copytree(ROOT / "Interview_Product_Manager_Kit", week8 / "Interview_Product_Manager_Kit")
    shutil.copytree(ROOT / "docs" / "evidence", week8 / "UI_and_Test_Evidence")
    shutil.copytree(ROOT / "demo_data" / "week1_final_demo", week8 / "Week1_Demo_Data")

    with zipfile.ZipFile(PORTFOLIO_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=7) as archive:
        _write_tree(archive, PORTFOLIO, Path("Offline_Retrieval_Week1-8_Portfolio"))


def build_final_folder() -> None:
    _safe_reset(FINAL)
    mapping = [
        MANAGER / "01_Week8_最终交付与全周期产品技术报告.pdf",
        WINDOWS_ZIP,
        SOURCE_ZIP,
        MANAGER / "04_Week8_Windows演示与录制操作手册.pdf",
        PORTFOLIO_ZIP,
        MANAGER / "06_Week8_最终测试发布与跨平台证据报告.pdf",
        MANAGER / "07_Week8_产品经理与技术经理面试手册.pdf",
    ]
    for path in mapping:
        if not path.is_file():
            raise FileNotFoundError(path)
        shutil.copy2(path, FINAL / path.name)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    MANAGER.mkdir(exist_ok=True)
    build_source_zip()
    build_windows_zip()
    build_portfolio()
    build_final_folder()
    files = []
    for path in sorted(FINAL.iterdir()):
        files.append({"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest = {
        "generated_at": date.today().isoformat(),
        "submission_date": SUBMISSION_DATE,
        "version": "1.0.0",
        "exact_final_file_count": len(files),
        "files": files,
        "owner_actions": [
            "Record and attach the final five-minute Windows demonstration video.",
            "Review and push the GitHub-ready source package to the intended public repository.",
            "Replace macOS/Linux simulation claims only after native runner artifacts exist.",
        ],
    }
    (ROOT / "reports" / "final_package_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if len(files) == 7 else 1


if __name__ == "__main__":
    raise SystemExit(main())
