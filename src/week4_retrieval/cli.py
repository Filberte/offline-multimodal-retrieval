"""Week4 索引与检索命令行入口。"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from week3_embedding.backends import HashingTextBackend, MobileCLIPBackend, TFLiteBertBackend
from week3_embedding.engine import EmbeddingEngine
from week3_embedding.vector_store import ChromaVectorStore
from week4_retrieval.models import SearchFilters, SearchQuery
from week4_retrieval.repository import ChromaRetrievalRepository
from week4_retrieval.service import CoreRetrievalService


# 解析索引或检索子命令，并以 JSON 输出执行结果。
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Week4 offline hybrid retrieval MVP")
    parser.add_argument("--db", default="data/chroma", help="Chroma 本地持久化目录")
    parser.add_argument("--backend", choices=("reference", "bert-tflite"), default="reference")
    parser.add_argument("--bert-model", help="Week3 BERT TFLite 模型路径")
    parser.add_argument("--bert-snapshot", help="本地 BERT tokenizer snapshot")
    parser.add_argument("--mobileclip-checkpoint", help="可选本地 MobileCLIP checkpoint")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="解析、嵌入并索引本地目录")
    index_parser.add_argument("path")
    index_parser.add_argument("--non-recursive", action="store_true")

    search_parser = subparsers.add_parser("search", help="执行混合检索")
    search_parser.add_argument("query")
    search_parser.add_argument("--top-k", type=int, default=5)
    search_parser.add_argument("--content-type")
    search_parser.add_argument("--extension")
    search_parser.add_argument("--text-only", action="store_true")
    args = parser.parse_args(argv)

    engine = _build_engine(args, parser)
    store = ChromaVectorStore(Path(args.db))
    service = CoreRetrievalService(
        engine=engine,
        repository=ChromaRetrievalRepository(store),
    )
    if args.command == "index":
        result = service.index_directory(
            args.path,
            recursive=not args.non_recursive,
        )
        payload = asdict(result)
        payload["success"] = result.success
    else:
        request = SearchQuery(
            text=args.query,
            top_k=args.top_k,
            include_cross_modal=not args.text_only,
            filters=SearchFilters(
                content_type=args.content_type,
                extension=args.extension,
            ),
        )
        payload = service.search(request).to_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


# 根据命令行参数构造离线文本与可选跨模态嵌入后端。
def _build_engine(args: argparse.Namespace, parser: argparse.ArgumentParser) -> EmbeddingEngine:
    if args.backend == "reference":
        text_backend = HashingTextBackend()
    else:
        if not args.bert_model or not args.bert_snapshot:
            parser.error("bert-tflite 需要 --bert-model 和 --bert-snapshot")
        text_backend = TFLiteBertBackend(args.bert_model, args.bert_snapshot)

    mobileclip = None
    if args.mobileclip_checkpoint:
        mobileclip = MobileCLIPBackend(args.mobileclip_checkpoint)
    return EmbeddingEngine(
        text_backend=text_backend,
        image_backend=mobileclip,
        cross_modal_text_backend=mobileclip,
    )


if __name__ == "__main__":
    raise SystemExit(main())
