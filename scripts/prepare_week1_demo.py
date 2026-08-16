"""Prepare the deterministic final demo directory from Week 1 datasets."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from week8_delivery.datasets import dataset_inventory, prepare_demo_dataset  # noqa: E402


def main() -> int:
    destination = ROOT / "demo_data" / "week1_final_demo"
    payload = prepare_demo_dataset(PROJECT_ROOT, destination)
    inventory = [item.to_dict() for item in dataset_inventory(PROJECT_ROOT)]
    report = {"inventory": inventory, "demo": payload, "passed": all(item["available"] for item in inventory) and payload["total_files"] == 22}
    output = ROOT / "reports" / "week1_demo_preparation.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"demo_root": str(destination), "files": payload["total_files"], "datasets": payload["by_dataset"], "passed": report["passed"]}, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
