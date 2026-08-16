"""构造使用本地模型和 Chroma 的 Week 6 生产服务。"""

from __future__ import annotations

import os
from pathlib import Path
from threading import RLock
from typing import Sequence

from week3_embedding.backends import HashingTextBackend, ImageBackend, TextBackend
from week3_embedding.engine import EmbeddingEngine
from week3_embedding.vector_store import ChromaVectorStore
from week4_retrieval.repository import ChromaRetrievalRepository
from week4_retrieval.service import CoreRetrievalService
from week6_integration.bridge import BridgeApplication
from week6_integration.embedding import CachedEmbeddingEngine
from week6_integration.security import OfflineSecurityPolicy
from week6_integration.service import IntegratedRetrievalService


class LazyTFLiteTextBackend(TextBackend):
    """首次文本请求时才加载 110 MB 本地 TFLite 模型。"""

    model_name = "bert-base-uncased-tflite"
    space = "bert-base-mean-pool-v1"

    def __init__(self, model_path: Path, tokenizer_path: Path) -> None:
        self.model_path = model_path
        self.tokenizer_path = tokenizer_path
        self._backend = None
        self._lock = RLock()

    def embed_texts(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        return self._load().embed_texts(texts)

    def _load(self):
        with self._lock:
            if self._backend is None:
                from week3_embedding.backends import TFLiteBertBackend

                self._backend = TFLiteBertBackend(self.model_path, self.tokenizer_path)
            return self._backend


class LazyMobileClipBackend(TextBackend, ImageBackend):
    """仅在跨模态请求到达时加载本地 MobileCLIP 权重。"""

    model_name = "MobileCLIP-S1"
    space = "mobileclip-s1-shared-v1"

    def __init__(self, checkpoint_path: Path) -> None:
        self.checkpoint_path = checkpoint_path
        self._backend = None
        self._lock = RLock()

    def embed_texts(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        return self._load().embed_texts(texts)

    def embed_images(self, image_paths: Sequence[str | Path]) -> tuple[tuple[float, ...], ...]:
        return self._load().embed_images(image_paths)

    def _load(self):
        with self._lock:
            if self._backend is None:
                from week3_embedding.backends import MobileCLIPBackend

                self._backend = MobileCLIPBackend(self.checkpoint_path)
            return self._backend


def build_service(root: str | Path | None = None) -> IntegratedRetrievalService:
    """按发布包与工作区中的本地资源选择生产模型，并保持确定性回退。"""

    delivery_root = Path(root).resolve() if root else Path(__file__).resolve().parents[2]
    project_root = delivery_root.parent
    backend_mode = os.environ.get("WEEK6_EMBEDDING_BACKEND", "auto").casefold()
    model_path = _first_existing_file(
        delivery_root / "models" / "bert_base_uncased_mean_pool_64.tflite",
        project_root / "Week3_Deliverables" / "models" / "bert_base_uncased_mean_pool_64.tflite",
    )
    tokenizer_path = _first_existing_directory(
        delivery_root / "models" / "bert_tokenizer",
        _first_snapshot(
            project_root / ".model_cache_week3" / "hub" / "models--google-bert--bert-base-uncased" / "snapshots"
        ),
    )
    mobile_path = _first_existing_file(
        delivery_root / "models" / "open_clip_model.safetensors",
        _find_file(
            project_root / ".model_cache_week3" / "hub" / "models--apple--MobileCLIP-S1-OpenCLIP" / "snapshots",
            "open_clip_model.safetensors",
        ),
    )

    if backend_mode not in {"auto", "tflite", "hashing"}:
        raise ValueError("WEEK6_EMBEDDING_BACKEND must be auto, tflite, or hashing")
    if backend_mode == "tflite" and (model_path is None or tokenizer_path is None):
        raise FileNotFoundError("local TFLite BERT model or tokenizer is missing")
    if backend_mode == "hashing" or model_path is None or tokenizer_path is None:
        text_backend = HashingTextBackend(dimension=128)
    else:
        text_backend = LazyTFLiteTextBackend(model_path, tokenizer_path)

    mobile_backend = LazyMobileClipBackend(mobile_path) if mobile_path else None
    engine = CachedEmbeddingEngine(
        EmbeddingEngine(
            text_backend=text_backend,
            image_backend=mobile_backend,
            cross_modal_text_backend=mobile_backend,
        ),
        cache_size=2048,
    )
    dimensions = {text_backend.space: 128 if isinstance(text_backend, HashingTextBackend) else 768}
    if mobile_backend is not None:
        dimensions[mobile_backend.space] = 512
    store = _build_offline_vector_store(
        Path(os.environ.get("OFFLINE_RETRIEVAL_DATA_DIR", str(delivery_root / "data" / "chroma_week8"))),
        dimensions,
    )
    core = CoreRetrievalService(
        engine=engine,
        repository=ChromaRetrievalRepository(store),
        batch_size=32,
        candidate_multiplier=4,
    )
    return IntegratedRetrievalService(core, query_cache_size=512, file_batch_size=64)


def build_application(root: str | Path | None = None) -> BridgeApplication:
    delivery_root = Path(root).resolve() if root else Path(__file__).resolve().parents[2]
    allowed = [delivery_root, delivery_root.parent, Path.home()]
    configured = os.environ.get("OFFLINE_RETRIEVAL_ALLOWED_ROOTS", "")
    if configured:
        allowed.extend(Path(item) for item in configured.split(os.pathsep) if item.strip())
    return BridgeApplication(build_service(delivery_root), OfflineSecurityPolicy(allowed))


def _build_offline_vector_store(
    persist_directory: Path,
    dimensions: dict[str, int],
) -> ChromaVectorStore:
    """创建显式关闭匿名遥测的本地持久化 Chroma 客户端。"""

    import chromadb
    from chromadb.config import Settings

    persist_directory.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(persist_directory),
        settings=Settings(anonymized_telemetry=False),
    )
    return ChromaVectorStore(
        persist_directory,
        client=client,
        expected_dimensions=dimensions,
    )


def _first_snapshot(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    return next((path for path in sorted(root.iterdir()) if path.is_dir()), None)


def _find_file(root: Path, name: str) -> Path | None:
    if not root.is_dir():
        return None
    return next((path for path in root.rglob(name) if path.is_file()), None)


def _first_existing_file(*paths: Path | None) -> Path | None:
    return next((path for path in paths if path is not None and path.is_file()), None)


def _first_existing_directory(*paths: Path | None) -> Path | None:
    return next((path for path in paths if path is not None and path.is_dir()), None)
