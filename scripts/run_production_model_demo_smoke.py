"""Run the Week 1 demo with the real local BERT/MobileCLIP production assembly."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ["WEEK6_EMBEDDING_BACKEND"] = "auto"
os.environ["OFFLINE_RETRIEVAL_DATA_DIR"] = str(ROOT / "data" / "production_demo_chroma")

from week4_retrieval.models import SearchFilters, SearchQuery  # noqa: E402
from week6_integration.factory import build_application  # noqa: E402
from week8_delivery.datasets import DEMO_QUERIES  # noqa: E402


def main() -> int:
    demo = ROOT / "demo_data" / "week1_final_demo"
    files = tuple(path for path in sorted(demo.rglob("*")) if path.is_file() and path.suffix.casefold() in {".txt", ".jpg", ".png"})
    started = time.perf_counter()
    application = build_application(ROOT)
    health_before = application.service.health().to_dict()
    indexing = application.service.index_paths(files, continue_on_error=True)
    query_results = []
    for item in DEMO_QUERIES:
        image_mode = item["mode"] == "image"
        response = application.service.search(
            SearchQuery(
                str(item["query"]),
                top_k=5,
                include_cross_modal=image_mode,
                filters=SearchFilters(modality="image") if image_mode else SearchFilters(),
            )
        )
        top_files = [str(hit.metadata.get("file_name", "")) for hit in response.hits]
        expected_file = item.get("expected_file")
        query_results.append({"query": item["query"], "mode": item["mode"], "hits": len(response.hits), "top_files": top_files, "expected_file": expected_file, "expected_file_rank": (top_files.index(expected_file) + 1 if expected_file in top_files else None)})
    health_after = application.service.health().to_dict()
    model_ready = health_after.get("backend_name") == "bert-base-uncased-tflite"
    images_succeeded = not any(".jpg" in message or ".png" in message for message in indexing.embedding_failures)
    passed = len(files) == 22 and indexing.discovered_files == 22 and indexing.parsed_files == 22 and not indexing.parse_failures and not indexing.embedding_failures and model_ready and images_succeeded and all(item["hits"] > 0 for item in query_results) and all(item["expected_file"] is None or item["expected_file_rank"] is not None for item in query_results)
    payload = {"generated_at": date.today().isoformat(), "method": "real_local_production_model_assembly", "models": {"text": health_after.get("backend_name"), "image": "MobileCLIP-S1 when image embedding succeeds"}, "offline_only": health_after.get("offline_only"), "files": len(files), "indexing": {"discovered": indexing.discovered_files, "parsed": indexing.parsed_files, "vectors": indexing.persisted_vectors, "parse_failures": list(indexing.parse_failures), "embedding_failures": list(indexing.embedding_failures)}, "health_before": health_before, "health_after": health_after, "queries": query_results, "elapsed_seconds": round(time.perf_counter() - started, 3), "passed": passed}
    output = ROOT / "reports" / "production_model_demo_smoke.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
