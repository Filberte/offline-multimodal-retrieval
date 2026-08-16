"""Validate the Week 1 demo files through parsing, embedding, Chroma, and retrieval."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from week3_embedding.backends import HashingTextBackend, ImageBackend  # noqa: E402
from week3_embedding.engine import EmbeddingEngine  # noqa: E402
from week3_embedding.math_utils import l2_normalize  # noqa: E402
from week3_embedding.vector_store import ChromaVectorStore  # noqa: E402
from week4_retrieval.models import SearchFilters, SearchQuery  # noqa: E402
from week4_retrieval.repository import ChromaRetrievalRepository  # noqa: E402
from week4_retrieval.service import CoreRetrievalService  # noqa: E402
from week6_integration.embedding import CachedEmbeddingEngine  # noqa: E402
from week6_integration.service import IntegratedRetrievalService  # noqa: E402
from week8_delivery.datasets import DEMO_QUERIES  # noqa: E402


class ValidationMultimodalBackend(HashingTextBackend, ImageBackend):
    """Deterministic test double; production execution continues to use local MobileCLIP."""

    model_name = "week8-validation-multimodal"
    space = "week8-validation-multimodal-v1"

    def embed_images(self, image_paths):
        vectors = []
        for raw_path in image_paths:
            digest = hashlib.sha256(Path(raw_path).read_bytes()).digest()
            values = [(digest[index % len(digest)] - 127.5) / 127.5 for index in range(self.dimension)]
            vectors.append(l2_normalize(values))
        return tuple(vectors)


def main() -> int:
    demo = ROOT / "demo_data" / "week1_final_demo"
    files = tuple(path for path in sorted(demo.rglob("*")) if path.is_file() and path.suffix.casefold() in {".txt", ".jpg", ".png"})
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="week8_demo_validation_", ignore_cleanup_errors=True) as temp:
        cross = ValidationMultimodalBackend(dimension=64)
        engine = CachedEmbeddingEngine(EmbeddingEngine(text_backend=HashingTextBackend(dimension=64), image_backend=cross, cross_modal_text_backend=cross), cache_size=512)
        store = ChromaVectorStore(Path(temp) / "chroma", expected_dimensions={"reference-text-v1": 64, cross.space: 64})
        service = IntegratedRetrievalService(CoreRetrievalService(engine=engine, repository=ChromaRetrievalRepository(store), batch_size=16, candidate_multiplier=4), file_batch_size=16)
        summary = service.index_paths(files)
        results = []
        for query in DEMO_QUERIES:
            image_mode = query["mode"] == "image"
            response = service.search(SearchQuery(str(query["query"]), top_k=5, include_cross_modal=image_mode, filters=SearchFilters(modality="image") if image_mode else SearchFilters()))
            expected_group = str(query["expected_group"])
            group_present = any(expected_group in hit.metadata.get("source_path", "").casefold() for hit in response.hits)
            results.append({"query": query["query"], "mode": query["mode"], "hits": len(response.hits), "group_present": group_present, "top_files": [hit.metadata.get("file_name") for hit in response.hits[:3]]})
        library = service.library_items()
    passed = len(files) == 22 and summary.discovered_files == 22 and summary.parsed_files == 22 and not summary.parse_failures and not summary.embedding_failures and len(library) == 22 and all(item["hits"] > 0 and item["group_present"] for item in results)
    payload = {"generated_at": date.today().isoformat(), "method": "deterministic_pipeline_validation_not_model_accuracy_claim", "lineage": "Week 1 data -> Week 2 parser -> Week 3 embedding interface -> Chroma -> Week 4 hybrid retrieval -> Week 6 integration", "files": len(files), "indexing": {"discovered": summary.discovered_files, "parsed": summary.parsed_files, "vectors": summary.persisted_vectors, "parse_failures": list(summary.parse_failures), "embedding_failures": list(summary.embedding_failures)}, "queries": results, "elapsed_seconds": round(time.perf_counter() - started, 3), "passed": passed}
    output = ROOT / "reports" / "week1_demo_validation.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
