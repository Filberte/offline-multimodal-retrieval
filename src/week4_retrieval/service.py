"""串联 Week2 解析、Week3 嵌入与 Week4 检索的核心服务。"""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Iterable, Sequence

from week2_parser.ingestion import discover_files, ingest_files
from week3_embedding.engine import EmbeddingEngine
from week3_embedding.integration import inputs_from_parse_result
from week3_embedding.models import EmbeddingInput, Modality
from week3_embedding.streaming import BoundedEmbeddingPipeline
from week4_retrieval.keyword import BM25Index
from week4_retrieval.models import IndexingSummary, SearchQuery, SearchResponse
from week4_retrieval.ranking import HybridRanker
from week4_retrieval.repository import ChromaRetrievalRepository


class CoreRetrievalService:
    """Week4 可运行 MVP，也是 Week5 UI 的稳定业务接口。"""

    # 组合嵌入引擎、检索仓储、批大小与候选扩展策略。
    def __init__(
        self,
        *,
        engine: EmbeddingEngine,
        repository: ChromaRetrievalRepository,
        batch_size: int = 16,
        candidate_multiplier: int = 5,
    ) -> None:
        if batch_size <= 0 or candidate_multiplier <= 0:
            raise ValueError("batch_size and candidate_multiplier must be positive")
        self.engine = engine
        self.repository = repository
        self.batch_size = batch_size
        self.candidate_multiplier = candidate_multiplier
        self.ranker = HybridRanker()

    # 串联 Week2 解析、Week3 嵌入和 Chroma 写入，对指定路径建立索引。
    def index_paths(
        self,
        paths: Iterable[str | Path],
        *,
        continue_on_error: bool = True,
    ) -> IndexingSummary:
        materialized = tuple(Path(path) for path in paths)
        ingestion = ingest_files(materialized, continue_on_error=continue_on_error)
        inputs: list[EmbeddingInput] = []
        for parse_result in ingestion.parsed:
            inputs.extend(inputs_from_parse_result(parse_result))

        # 文本和图片分别切批；底层仍通过 Week3 统一 EmbeddingEngine 调度。
        text_inputs = [item for item in inputs if item.modality is Modality.TEXT]
        image_inputs = [item for item in inputs if item.modality is Modality.IMAGE]
        pipeline = BoundedEmbeddingPipeline(
            self.engine,
            store=self.repository.store,
            batch_size=self.batch_size,
        )
        persisted = 0
        failures: list[dict[str, str]] = []
        for group in (text_inputs, image_inputs):
            for batch in pipeline.iter_batches(
                group,
                space="default",
                continue_on_error=continue_on_error,
            ):
                persisted += batch.persisted_vectors
                failures.extend(
                    {
                        "item_id": failure.item_id,
                        "error_type": failure.error_type,
                        "error": failure.error,
                    }
                    for failure in batch.result.failures
                )

        return IndexingSummary(
            discovered_files=len(materialized),
            parsed_files=len(ingestion.parsed),
            parse_failures=ingestion.failed,
            embedding_inputs=len(inputs),
            embedding_failures=tuple(failures),
            persisted_vectors=persisted,
        )

    # 发现目录中的受支持文件，并复用路径索引流程完成批量入库。
    def index_directory(
        self,
        root: str | Path,
        *,
        recursive: bool = True,
        continue_on_error: bool = True,
    ) -> IndexingSummary:
        paths = discover_files(root, recursive=recursive)
        return self.index_paths(paths, continue_on_error=continue_on_error)

    # 执行文本语义召回、可选跨模态召回、BM25 与融合排序。
    def search(self, request: SearchQuery) -> SearchResponse:
        request.validate()
        started = perf_counter()
        warnings: list[str] = []
        candidate_limit = max(20, request.top_k * self.candidate_multiplier)
        where = request.filters.to_chroma_where()

        # 默认文本查询进入 BERT 空间。
        query_input = EmbeddingInput(
            item_id="week4-query",
            modality=Modality.TEXT,
            text=request.text,
        )
        text_vector = self.engine.embed(query_input, space="default")
        semantic = list(
            self.repository.semantic_search(
                space=text_vector.space,
                query_embedding=text_vector.values,
                n_results=candidate_limit,
                where=where,
            )
        )

        # 仅当配置了 MobileCLIP 文本编码器时召回图片，且保持空间内计算。
        if request.include_cross_modal:
            if self.engine.cross_modal_text_backend is None:
                warnings.append("未配置 MobileCLIP 文本编码器，本次仅检索文本空间。")
            else:
                cross_vector = self.engine.embed(query_input, space="cross_modal")
                semantic.extend(
                    self.repository.semantic_search(
                        space=cross_vector.space,
                        query_embedding=cross_vector.values,
                        n_results=candidate_limit,
                        where=where,
                    )
                )

        # BM25 只读取文本空间；图像没有可靠正文时不制造伪关键词分数。
        lexical_records = self.repository.scan(space=text_vector.space, where=where)
        lexical_records = tuple(
            record for record in lexical_records if request.filters.accepts(record.metadata)
        )
        semantic = [
            candidate
            for candidate in semantic
            if request.filters.accepts(candidate.record.metadata)
        ]
        keyword_matches = BM25Index(lexical_records).search(
            request.text,
            limit=candidate_limit,
        )
        hits = self.ranker.rank(
            semantic=semantic,
            keyword=keyword_matches,
            semantic_weight=request.semantic_weight,
            keyword_weight=request.keyword_weight,
            top_k=request.top_k,
        )
        elapsed_ms = (perf_counter() - started) * 1000
        unique_candidates = {
            (candidate.record.space, candidate.record.item_id) for candidate in semantic
        }
        unique_candidates.update(
            (match.record.space, match.record.item_id) for match in keyword_matches
        )
        return SearchResponse(
            query=request.text,
            hits=hits,
            elapsed_ms=round(elapsed_ms, 3),
            candidate_count=len(unique_candidates),
            warnings=tuple(warnings),
        )
