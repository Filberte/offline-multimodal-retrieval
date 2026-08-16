"""适用于 SQuAD/NQ 风格文本与 COCO 图像的检索验证指标。"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from week3_embedding.backends import ImageBackend, TextBackend
from week3_embedding.math_utils import cosine_similarity


@dataclass(frozen=True)
class RetrievalMetrics:
    # 统一记录召回率、平均倒数排名、耗时和吞吐量。
    samples: int
    recall_at_1: float
    recall_at_5: float
    mean_reciprocal_rank: float
    elapsed_seconds: float

    def as_dict(self) -> dict[str, float | int]:
        return {
            "samples": self.samples,
            "recall_at_1": round(self.recall_at_1, 4),
            "recall_at_5": round(self.recall_at_5, 4),
            "mean_reciprocal_rank": round(self.mean_reciprocal_rank, 4),
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "items_per_second": round(self.samples / self.elapsed_seconds, 3) if self.elapsed_seconds else 0.0,
        }


def validate_squad(
    text_backend: TextBackend,
    qa_csv: str | Path,
    *,
    contexts_dir: str | Path | None = None,
    limit: int = 40,
) -> RetrievalMetrics:
    # 问题作为查询，去重后的上下文作为候选文档。
    rows = _read_squad_rows(qa_csv, limit, contexts_dir)
    contexts: list[str] = []
    context_index: dict[str, int] = {}
    questions: list[str] = []
    expected: list[int] = []
    for question, context in rows:
        if context not in context_index:
            context_index[context] = len(contexts)
            contexts.append(context)
        questions.append(question)
        expected.append(context_index[context])
    started = time.perf_counter()
    context_vectors = text_backend.embed_texts(contexts)
    question_vectors = text_backend.embed_texts(questions)
    return _rank_metrics(question_vectors, context_vectors, expected, time.perf_counter() - started)


def validate_coco(
    shared_backend: TextBackend,
    image_backend: ImageBackend,
    captions_json: str | Path,
    image_dir: str | Path,
    *,
    limit: int = 20,
) -> RetrievalMetrics:
    # 每张本地图像只取一条 caption，构建一对一检索样本。
    payload = json.loads(Path(captions_json).read_text(encoding="utf-8"))
    image_names = {int(item["id"]): item["file_name"] for item in payload["images"]}
    samples: list[tuple[str, Path]] = []
    seen: set[int] = set()
    for annotation in payload["annotations"]:
        image_id = int(annotation["image_id"])
        path = Path(image_dir) / image_names[image_id]
        if image_id in seen or not path.is_file():
            continue
        seen.add(image_id)
        samples.append((str(annotation["caption"]), path))
        if len(samples) >= limit:
            break
    started = time.perf_counter()
    text_vectors = shared_backend.embed_texts([caption for caption, _ in samples])
    image_vectors = image_backend.embed_images([path for _, path in samples])
    expected = list(range(len(samples)))
    return _rank_metrics(text_vectors, image_vectors, expected, time.perf_counter() - started)


def _rank_metrics(
    queries: Sequence[Sequence[float]],
    candidates: Sequence[Sequence[float]],
    expected: Sequence[int],
    elapsed: float,
) -> RetrievalMetrics:
    if len(queries) != len(expected) or not queries or not candidates:
        raise ValueError("queries, candidates, and expected matches must be non-empty and aligned")
    # 对每个查询按余弦相似度降序排列并记录正确候选名次。
    ranks: list[int] = []
    for query, target in zip(queries, expected):
        ordered = sorted(
            range(len(candidates)),
            key=lambda index: cosine_similarity(query, candidates[index]),
            reverse=True,
        )
        ranks.append(ordered.index(target) + 1)
    total = len(ranks)
    return RetrievalMetrics(
        samples=total,
        recall_at_1=sum(rank <= 1 for rank in ranks) / total,
        recall_at_5=sum(rank <= 5 for rank in ranks) / total,
        mean_reciprocal_rank=sum(1 / rank for rank in ranks) / total,
        elapsed_seconds=elapsed,
    )


def _read_squad_rows(
    path: str | Path,
    limit: int,
    contexts_dir: str | Path | None = None,
) -> list[tuple[str, str]]:
    # 上下文文件按 context_id 缓存，减少重复磁盘读取。
    context_cache: dict[str, str] = {}
    seen_context_ids: set[str] = set()
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            question = row.get("question", "").strip()
            context_id = row.get("context_id", "").strip()
            if contexts_dir is not None and context_id in seen_context_ids:
                continue
            context = row.get("context", "").strip()
            if not context and contexts_dir is not None:
                if context_id not in context_cache:
                    matches = sorted(Path(contexts_dir).glob(f"{int(context_id):04d}_*.txt")) if context_id else []
                    context_cache[context_id] = matches[0].read_text(encoding="utf-8") if matches else ""
                context = context_cache[context_id].strip()
            if question and context:
                rows.append((question, context))
                if context_id:
                    seen_context_ids.add(context_id)
            if len(rows) >= limit:
                break
    if not rows:
        raise ValueError("SQuAD CSV did not contain question/context rows")
    return rows
