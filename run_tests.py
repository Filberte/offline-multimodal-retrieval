"""Run the cumulative 600-case Python and Flutter production test suite."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
FLUTTER_APP = ROOT / "app" / "offline_retrieval_ui"
FLUTTER_BIN = ROOT.parent / "dev_env/flutter/bin/flutter.bat"
PUB_CACHE = ROOT.parent / "dev_env/pub-cache"


def _run(command: list[str], *, cwd: Path, output: Path, env: dict[str, str]) -> tuple[int, float]:
    started = time.perf_counter()
    process = subprocess.run(command, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
    elapsed = time.perf_counter() - started
    text = process.stdout + process.stderr
    output.write_text(text, encoding="utf-8")
    print(text, end="")
    return process.returncode, elapsed


def _catalog() -> list[dict[str, str]]:
    cases: list[dict[str, str]] = []
    python_pattern = re.compile(r"def\s+test_(\d{3})_([a-zA-Z0-9_]+)")
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        for case_id, name in python_pattern.findall(path.read_text(encoding="utf-8")):
            cases.append({"id": f"TC-{case_id}", "name": name, "layer": "Python retrieval and delivery core", "source": str(path.relative_to(ROOT))})
    dart_pattern = re.compile(r"(?:test|testWidgets)\('TC-(\d{3})\s+([^']+)'")
    for path in sorted((FLUTTER_APP / "test").glob("*_test.dart")):
        for case_id, name in dart_pattern.findall(path.read_text(encoding="utf-8")):
            cases.append({"id": f"TC-{case_id}", "name": name, "layer": "Flutter UI and accessibility", "source": str(path.relative_to(ROOT))})
    return sorted(cases, key=lambda item: int(item["id"].split("-")[1]))


def _flutter_coverage() -> dict[str, float | int]:
    path = FLUTTER_APP / "coverage/lcov.info"
    found = covered = 0
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("LF:"):
                found += int(line[3:])
            elif line.startswith("LH:"):
                covered += int(line[3:])
    return {"statements": found, "covered": covered, "coverage_percent": round(covered / found * 100 if found else 0, 2)}


def main() -> int:
    REPORTS.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.update({"PYTHONIOENCODING": "utf-8", "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "safe.directory", "GIT_CONFIG_VALUE_0": str(ROOT.parent / "dev_env/flutter"), "PUB_CACHE": str(PUB_CACHE)})
    core_code, core_seconds = _run([sys.executable, str(ROOT / "run_core_tests.py"), "discover", "-s", str(ROOT / "tests"), "-v"], cwd=ROOT, output=REPORTS / "core_test_run.txt", env=env)
    flutter_code, flutter_seconds = _run([str(FLUTTER_BIN), "test", "--no-pub", "--coverage", "--reporter", "expanded", "--concurrency", "1"], cwd=FLUTTER_APP, output=REPORTS / "flutter_test_run.txt", env=env)
    cases = _catalog()
    numeric_ids = [int(item["id"].split("-")[1]) for item in cases]
    continuous = numeric_ids == list(range(1, 601))
    core_coverage = json.loads((REPORTS / "coverage_summary.json").read_text(encoding="utf-8"))
    summary = {"generated_at": date.today().isoformat(), "total_tests": len(cases), "passed_tests": len(cases) if core_code == 0 and flutter_code == 0 else None, "failed_tests": 0 if core_code == 0 and flutter_code == 0 else None, "continuous_ids_tc_001_to_tc_600": continuous, "core": {"tests": sum(1 for case in cases if case["layer"].startswith("Python")), "passed": core_code == 0, "elapsed_seconds": round(core_seconds, 3), "coverage_percent": core_coverage["coverage_percent"]}, "flutter": {"tests": sum(1 for case in cases if case["layer"].startswith("Flutter")), "passed": flutter_code == 0, "elapsed_seconds": round(flutter_seconds, 3), **_flutter_coverage()}, "all_passed": core_code == 0 and flutter_code == 0 and continuous}
    (REPORTS / "test_case_catalog.json").write_text(json.dumps(cases, indent=2, ensure_ascii=False), encoding="utf-8")
    (REPORTS / "combined_test_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWeek 8 cumulative total: {summary['total_tests']} tests; all passed: {summary['all_passed']}")
    return 0 if summary["all_passed"] and len(cases) == 600 else 1


if __name__ == "__main__":
    raise SystemExit(main())
