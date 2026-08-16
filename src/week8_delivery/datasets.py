"""Week 1 dataset inventory and deterministic Windows demo subset builder."""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from week8_delivery.models import DatasetSummary


DATASET_CONFIG = {
    "squad": {
        "display_name": "SQuAD 2.0（经批准替代 NQ）",
        "role": "文本嵌入与问答式检索",
        "expected": 200,
        "pattern": "processed/contexts/*.txt",
        "manifest": "metadata/manifest.json",
        "note": "Week 1 记录了 NQ 下载 403，经理批准使用 SQuAD 2.0。",
    },
    "coco": {
        "display_name": "COCO 2017 validation subset",
        "role": "图像嵌入与跨模态检索",
        "expected": 50,
        "pattern": "raw/images/val2017/*",
        "manifest": "metadata/manifest.json",
        "note": "50 张官方 COCO validation 图像。",
    },
    "rvl_cdip": {
        "display_name": "RVL-CDIP-N related subset",
        "role": "扫描文档图像检索与 OCR 边界验证",
        "expected": 50,
        "pattern": "raw/images/test/*",
        "manifest": "metadata/manifest.json",
        "note": "与 RVL-CDIP 相关的小型本地子集，不等同完整 38.8 GB RVL-CDIP。",
    },
    "wikipedia": {
        "display_name": "Wikipedia text corpus subset",
        "role": "长文解析、分块与批处理性能",
        "expected": 100,
        "pattern": "processed/articles/*.txt",
        "manifest": "metadata/manifest.json",
        "note": "从 Wikimedia 官方 dump shard 抽取的 100 篇文章。",
    },
}


DEMO_SELECTION = {
    "squad": (
        "processed/contexts/0000_Normans.txt",
        "processed/contexts/0001_Normans.txt",
        "processed/contexts/0004_Normans.txt",
        "processed/contexts/0007_Normans.txt",
        "processed/contexts/0011_Normans.txt",
        "processed/contexts/0018_Normans.txt",
    ),
    "wikipedia": (
        "processed/articles/000_Anarchism.txt",
        "processed/articles/003_Alabama.txt",
        "processed/articles/005_Abraham_Lincoln.txt",
        "processed/articles/006_Aristotle.txt",
    ),
    "coco": (
        "raw/images/val2017/000000397133.jpg",
        "raw/images/val2017/000000087038.jpg",
        "raw/images/val2017/000000386912.jpg",
        "raw/images/val2017/000000348881.jpg",
        "raw/images/val2017/000000522713.jpg",
        "raw/images/val2017/000000480985.jpg",
    ),
    "rvl_cdip": tuple(
        f"raw/images/test/rvl_cdip_n_test_{index:05d}_budget.png"
        for index in range(6)
    ),
}


DEMO_QUERIES = (
    {
        "query": "Norman conquest of England",
        "mode": "text",
        "expected_group": "squad",
        "narration": "验证 Week 2 文本解析、Week 3 文本嵌入和 Week 4 混合排序。",
    },
    {
        "query": "Abraham Lincoln president",
        "mode": "text",
        "expected_group": "wikipedia",
        "narration": "验证长文分块、持久化和可解释来源。",
    },
    {
        "query": "an airplane parked at an airport gate",
        "mode": "image",
        "expected_group": "coco",
        "expected_file": "000000348881.jpg",
        "narration": "验证 COCO 自然图像的文本到图像跨模态搜索。",
    },
    {
        "query": "budget document",
        "mode": "image",
        "expected_group": "rvl_cdip",
        "expected_file": "rvl_cdip_n_test_00004_budget.png",
        "narration": "验证 RVL-CDIP 相关扫描文档图像检索，并明确 OCR 尚未生产化。",
    },
)


def dataset_inventory(project_root: str | Path) -> tuple[DatasetSummary, ...]:
    root = Path(project_root).resolve()
    base = root / "datasets" / "required_datasets"
    records = []
    for key, config in DATASET_CONFIG.items():
        dataset_root = base / key
        files = tuple(path for path in dataset_root.glob(str(config["pattern"])) if path.is_file())
        manifest = dataset_root / str(config["manifest"])
        records.append(
            DatasetSummary(
                key=key,
                display_name=str(config["display_name"]),
                role=str(config["role"]),
                expected_samples=int(config["expected"]),
                discovered_samples=len(files),
                source_root=str(dataset_root),
                manifest_path=str(manifest),
                available=manifest.is_file() and len(files) >= int(config["expected"]),
                note=str(config["note"]),
            )
        )
    return tuple(records)


def default_demo_selection(project_root: str | Path) -> tuple[Path, ...]:
    base = Path(project_root).resolve() / "datasets" / "required_datasets"
    return tuple(base / dataset / relative for dataset, paths in DEMO_SELECTION.items() for relative in paths)


def prepare_demo_dataset(project_root: str | Path, destination: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    output = Path(destination).resolve()
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for dataset, paths in DEMO_SELECTION.items():
        for relative in paths:
            source = root / "datasets" / "required_datasets" / dataset / relative
            if not source.is_file():
                raise FileNotFoundError(source)
            target = output / dataset / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            entries.append(
                {
                    "dataset": dataset,
                    "source": str(source.relative_to(root)),
                    "demo_path": str(target.relative_to(output)),
                    "bytes": target.stat().st_size,
                }
            )
    payload = {
        "generated_at": date.today().isoformat(),
        "provenance": "Exact copies selected from the Week 1 curated local datasets",
        "project_root": str(root),
        "demo_root": str(output),
        "total_files": len(entries),
        "by_dataset": {key: len(paths) for key, paths in DEMO_SELECTION.items()},
        "entries": entries,
        "queries": list(DEMO_QUERIES),
    }
    (output / "week1_demo_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload
