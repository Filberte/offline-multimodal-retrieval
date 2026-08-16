"""Write explicit Windows-real/macOS-Linux-simulated platform evidence."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from week8_delivery.platforms import evaluate_platforms  # noqa: E402


def main() -> int:
    assessments = evaluate_platforms(ROOT)
    payload = {"generated_at": date.today().isoformat(), "host": "Windows", "assessments": [item.to_dict() for item in assessments], "truthfulness_notice": "Only Windows is real host build evidence. macOS and Linux results are source/configuration simulations until native CI or real-device artifacts are attached."}
    output = ROOT / "reports" / "platform_evidence.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if assessments[0].decision == "GO" and all(not item.blocking_failures for item in assessments[1:]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
