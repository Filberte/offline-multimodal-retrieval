"""Start the self-contained Week 8 local retrieval JSON-lines backend."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from week6_integration.bridge import serve_stdio  # noqa: E402
from week6_integration.factory import build_application  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline multimodal retrieval backend 1.0.0")
    parser.add_argument("--self-check", action="store_true", help="Print local backend health and exit")
    parser.add_argument("--root", type=Path, default=ROOT, help="Delivery root containing src, data, and optional models")
    arguments = parser.parse_args(argv)
    application = build_application(arguments.root)
    if arguments.self_check:
        print(json.dumps(application.service.health().to_dict(), ensure_ascii=False, indent=2))
        return 0
    return serve_stdio(application)


if __name__ == "__main__":
    raise SystemExit(main())
