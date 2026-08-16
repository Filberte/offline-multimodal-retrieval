"""完全离线的 BM25 关键词索引。"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Mapping

from week4_retrieval.models import StoredRecord


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_']+|[\u3400-\u9fff]")


def tokenize(text: str) -> tuple[str, ...]:
    """同时支持英文词项和中文单字的确定性分词。"""

    return tuple(token.casefold() for token in _TOKEN_PATTERN.findall(text))


@dataclass(frozen=True)
class KeywordMatch:
    record: StoredRecord
    score: float


class BM25Index:
    """轻量 BM25 实现，不需要网络、搜索服务或额外运行时。"""

    # 构建文档词项、平均长度和文档频率等不可变检索统计。
    def __init__(self, records: Iterable[StoredRecord], *, k1: float = 1.5, b: float = 0.75) -> None:
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("invalid BM25 parameters")
        self.k1 = k1
        self.b = b
        self._records = {record.item_id: record for record in records if record.document.strip()}
        self._tokens = {item_id: tokenize(record.document) for item_id, record in self._records.items()}
        lengths = [len(tokens) for tokens in self._tokens.values()]
        self._average_length = sum(lengths) / len(lengths) if lengths else 0.0
        self._document_frequency = self._build_document_frequency()

    @property
    # 返回实际进入关键词索引的非空文档数量。
    def document_count(self) -> int:
        return len(self._records)

    # 对查询执行 BM25 评分，并按分数和稳定记录标识返回候选。
    def search(self, query: str, *, limit: int | None = None) -> tuple[KeywordMatch, ...]:
        query_terms = tokenize(query)
        if not query_terms or not self._records:
            return ()
        scores: list[KeywordMatch] = []
        for item_id, terms in self._tokens.items():
            score = self._score_terms(terms, query_terms)
            if score > 0:
                scores.append(KeywordMatch(self._records[item_id], score))
        scores.sort(key=lambda match: (-match.score, match.record.item_id))
        return tuple(scores[:limit] if limit is not None else scores)

    # 汇总每个词项出现过的文档数量，用于计算逆文档频率。
    def _build_document_frequency(self) -> Mapping[str, int]:
        frequencies: Counter[str] = Counter()
        for terms in self._tokens.values():
            frequencies.update(set(terms))
        return frequencies

    # 计算单篇文档对当前查询词项集合的 BM25 原始分数。
    def _score_terms(self, terms: tuple[str, ...], query_terms: tuple[str, ...]) -> float:
        if not terms or self._average_length <= 0:
            return 0.0
        counts = Counter(terms)
        total_documents = len(self._records)
        score = 0.0
        for term in query_terms:
            frequency = counts.get(term, 0)
            if not frequency:
                continue
            document_frequency = self._document_frequency.get(term, 0)
            # Robertson/Sparck Jones IDF 加 1，避免高频词产生负分。
            idf = math.log(1 + (total_documents - document_frequency + 0.5) / (document_frequency + 0.5))
            denominator = frequency + self.k1 * (
                1 - self.b + self.b * len(terms) / self._average_length
            )
            score += idf * frequency * (self.k1 + 1) / denominator
        return score
