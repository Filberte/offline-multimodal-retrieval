"""Week 3 多模态嵌入引擎的公共 API 入口。"""

from week3_embedding.backends import HashingTextBackend, MobileCLIPBackend, TFLiteBertBackend, TorchBertBackend
from week3_embedding.engine import EmbeddingEngine
from week3_embedding.integration import inputs_from_parse_result, stable_document_id
from week3_embedding.math_utils import cosine_similarity
from week3_embedding.models import BatchEmbeddingResult, EmbeddingInput, EmbeddingVector, Modality

# 仅导出业务调用方需要的稳定接口，隐藏内部实现细节。
__all__ = [
    "BatchEmbeddingResult",
    "EmbeddingEngine",
    "EmbeddingInput",
    "EmbeddingVector",
    "HashingTextBackend",
    "MobileCLIPBackend",
    "Modality",
    "TFLiteBertBackend",
    "TorchBertBackend",
    "cosine_similarity",
    "inputs_from_parse_result",
    "stable_document_id",
]
