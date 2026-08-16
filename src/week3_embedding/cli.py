"""支持单条与批量嵌入处理的命令行入口。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from week3_embedding.backends import HashingTextBackend, MobileCLIPBackend, TFLiteBertBackend
from week3_embedding.engine import EmbeddingEngine
from week3_embedding.models import EmbeddingInput, Modality


def main() -> int:
    # 命令行参数同时覆盖参考后端、TFLite BERT 和 MobileCLIP 三种模式。
    parser = argparse.ArgumentParser(description="Week 3 offline embedding CLI")
    parser.add_argument("inputs", nargs="+", help="Text strings or local image paths")
    parser.add_argument("--backend", choices=("reference", "bert-tflite", "mobileclip"), default="reference")
    parser.add_argument("--model-path", help="Local .tflite or MobileCLIP checkpoint path")
    parser.add_argument("--tokenizer-path", help="Local BERT tokenizer/snapshot directory")
    parser.add_argument("--image", action="store_true", help="Treat inputs as image paths")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    if args.backend == "reference":
        # reference 后端无需模型文件，主要用于安装后快速自检。
        if args.image:
            parser.error("reference backend supports text only")
        engine = EmbeddingEngine(text_backend=HashingTextBackend())
        space = "default"
    elif args.backend == "bert-tflite":
        # 文本生产后端必须同时提供模型与本地 tokenizer。
        if args.image:
            parser.error("bert-tflite backend supports text only")
        if not args.model_path or not args.tokenizer_path:
            parser.error("bert-tflite requires --model-path and --tokenizer-path")
        bert = TFLiteBertBackend(args.model_path, args.tokenizer_path)
        engine = EmbeddingEngine(text_backend=bert)
        space = "default"
    else:
        # MobileCLIP 在同一向量空间中支持图文跨模态检索。
        if not args.model_path:
            parser.error("mobileclip requires --model-path")
        mobileclip = MobileCLIPBackend(args.model_path)
        engine = EmbeddingEngine(
            text_backend=mobileclip,
            image_backend=mobileclip,
            cross_modal_text_backend=mobileclip,
        )
        space = "cross_modal" if not args.image else "default"

    modality = Modality.IMAGE if args.image else Modality.TEXT
    # 将原始命令行输入转换为引擎统一数据契约。
    items = [
        EmbeddingInput(
            f"item-{index}",
            modality,
            image_path=value if args.image else None,
            text=None if args.image else value,
        )
        for index, value in enumerate(args.inputs)
    ]
    result = engine.embed_batch(items, space=space)
    # JSON 输出包含模型来源、空间和维度，便于 Week4 入库追踪。
    payload = {
        "total_items": result.total_items,
        "success_rate": result.success_rate,
        "vectors": [
            {
                "item_id": vector.item_id,
                "modality": vector.modality.value,
                "space": vector.space,
                "model_name": vector.model_name,
                "dimension": vector.dimension,
                "values": vector.values,
            }
            for vector in result.vectors
        ],
        "failures": [failure.__dict__ for failure in result.failures],
    }
    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0 if not result.failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
