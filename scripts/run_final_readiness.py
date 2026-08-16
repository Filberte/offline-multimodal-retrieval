"""Generate the final Week 1–8 lineage and Week 8 hand-off gate report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from week8_delivery.lineage import validate_lineage  # noqa: E402
from week8_delivery.platforms import evaluate_platforms  # noqa: E402
from week8_delivery.readiness import build_final_readiness  # noqa: E402


REQUIRED_DOCUMENTS = (
    "manager_submission/01_Week8_最终交付与全周期产品技术报告.pdf",
    "manager_submission/04_Week8_Windows演示与录制操作手册.pdf",
    "manager_submission/06_Week8_最终测试发布与跨平台证据报告.pdf",
    "manager_submission/07_Week8_产品经理与技术经理面试手册.pdf",
)


def main() -> int:
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    lineage = validate_lineage(PROJECT_ROOT)
    (reports / "week1_to_week8_lineage.json").write_text(
        json.dumps(lineage, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tests = json.loads(
        (reports / "combined_test_summary.json").read_text(encoding="utf-8")
    )
    readiness = build_final_readiness(
        ROOT,
        test_summary=tests,
        platforms=evaluate_platforms(ROOT),
        required_documents=REQUIRED_DOCUMENTS,
    )
    payload = readiness.to_dict()
    payload["claim_boundary"] = {
        "windows": "real host build and execution evidence",
        "macos": "Windows-hosted source/contract simulation; native artifact pending",
        "linux": "Windows-hosted source/contract simulation; native artifact pending",
        "github": "repository-ready package; public push pending owner authorization",
        "video": "script and runbook complete; final Windows recording pending owner",
    }
    (reports / "final_readiness.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if readiness.decision == "GO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
