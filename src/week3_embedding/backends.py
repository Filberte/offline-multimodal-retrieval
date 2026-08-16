"""离线嵌入后端：BERT/LiteRT、MobileCLIP 以及测试用参考模型。"""

from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, Sequence

from week3_embedding.math_utils import l2_normalize


# 文本后端抽象约束：所有实现必须返回逐条 L2 归一化向量。
class TextBackend(ABC):
    model_name: str
    space: str

    @abstractmethod
    def embed_texts(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        """为每段文本返回一个经过 L2 归一化的向量。"""


# 图像后端抽象约束，与文本后端共享统一的批处理返回格式。
class ImageBackend(ABC):
    model_name: str
    space: str

    @abstractmethod
    def embed_images(self, image_paths: Sequence[str | Path]) -> tuple[tuple[float, ...], ...]:
        """为每张图像返回一个经过 L2 归一化的向量。"""


class HashingTextBackend(TextBackend):
    """轻依赖且结果确定的文本后端，用于单元测试和紧急冒烟验证。"""

    model_name = "hashing-text-reference-v1"
    space = "reference-text-v1"

    def __init__(self, dimension: int = 128) -> None:
        if dimension < 8:
            raise ValueError("dimension must be at least 8")
        self.dimension = dimension

    def embed_texts(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        return tuple(self._embed(text) for text in texts)

    def _embed(self, text: str) -> tuple[float, ...]:
        # 使用稳定哈希完成带符号特征映射，保证离线测试可重复。
        vector = [0.0] * self.dimension
        tokens = re.findall(r"[\w']+", text.lower())
        if not tokens:
            raise ValueError("text must contain at least one token")
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(digest[:8], "little") % self.dimension
            sign = 1.0 if digest[8] & 1 else -1.0
            vector[index] += sign
        return l2_normalize(vector)


class TorchBertBackend(TextBackend):
    """作为 TFLite 转换与精度对照基线的 BERT-base CPU 后端。"""

    model_name = "google-bert/bert-base-uncased"
    space = "bert-base-mean-pool-v1"

    def __init__(
        self,
        model_path: str | Path,
        *,
        max_length: int = 64,
        batch_size: int = 8,
        torch_module=None,
        tokenizer=None,
        model=None,
    ) -> None:
        self.max_length = max_length
        self.batch_size = batch_size
        self._torch = torch_module or __import__("torch")
        if tokenizer is None or model is None:
            from transformers import AutoModel, AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
            model = AutoModel.from_pretrained(str(model_path), local_files_only=True)
        self._tokenizer = tokenizer
        self._model = model
        # 推理模式关闭训练期随机行为，确保同一输入结果稳定。
        self._model.eval()

    def embed_texts(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        if any(not text.strip() for text in texts):
            raise ValueError("texts must not be blank")
        vectors: list[tuple[float, ...]] = []
        torch = self._torch
        with torch.inference_mode():
            # 分批推理控制内存峰值，适配普通消费级 CPU 设备。
            for start in range(0, len(texts), self.batch_size):
                batch = list(texts[start : start + self.batch_size])
                tokens = self._tokenizer(
                    batch,
                    return_tensors="pt",
                    padding="max_length",
                    truncation=True,
                    max_length=self.max_length,
                )
                hidden = self._model(**tokens).last_hidden_state
                mask = tokens["attention_mask"].unsqueeze(-1)
                # 仅对非填充 token 做均值池化，再统一归一化向量。
                pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1)
                pooled = torch.nn.functional.normalize(pooled, dim=-1)
                vectors.extend(tuple(float(value) for value in row) for row in pooled.cpu().tolist())
        return tuple(vectors)


class TFLiteBertBackend(TextBackend):
    """通过 TFLite 解释器执行的 BERT-base 均值池化后端。"""

    model_name = "bert-base-uncased-tflite"
    space = "bert-base-mean-pool-v1"

    def __init__(
        self,
        model_path: str | Path,
        tokenizer_path: str | Path,
        *,
        max_length: int = 64,
        tokenizer=None,
        interpreter=None,
    ) -> None:
        if tokenizer is None:
            from transformers import AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_path), local_files_only=True)
        self.max_length = max_length
        self._tokenizer = tokenizer
        self._interpreter = interpreter or _create_tflite_interpreter(str(model_path))
        # 预先分配张量，避免每次请求重复初始化解释器。
        self._interpreter.allocate_tensors()
        self._inputs = self._interpreter.get_input_details()
        self._outputs = self._interpreter.get_output_details()

    def embed_texts(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        if any(not text.strip() for text in texts):
            raise ValueError("texts must not be blank")
        results: list[tuple[float, ...]] = []
        for text in texts:
            # 输入长度固定为 max_length，以匹配导出的 TFLite 张量形状。
            encoded = self._tokenizer(
                text,
                return_tensors="np",
                padding="max_length",
                truncation=True,
                max_length=self.max_length,
            )
            for detail in self._inputs:
                name = _match_input_name(detail["name"])
                self._interpreter.set_tensor(detail["index"], encoded[name].astype(detail["dtype"]))
            self._interpreter.invoke()
            output = self._interpreter.get_tensor(self._outputs[0]["index"])[0]
            results.append(l2_normalize(output.tolist()))
        return tuple(results)


class MobileCLIPBackend(TextBackend, ImageBackend):
    """通过 OpenCLIP 调用仅使用本地权重的官方 MobileCLIP 模型。"""

    space = "mobileclip-s1-shared-v1"
    model_name = "MobileCLIP-S1"

    def __init__(
        self,
        checkpoint_path: str | Path,
        *,
        batch_size: int = 8,
        torch_module=None,
        model=None,
        preprocess=None,
        tokenizer=None,
    ) -> None:
        if model is None:
            # 模型和检查点均从本地加载，运行阶段不访问网络。
            import open_clip
            import torch

            torch_module = torch_module or torch
            model, _, preprocess = open_clip.create_model_and_transforms(
                self.model_name, pretrained=str(checkpoint_path)
            )
            tokenizer = open_clip.get_tokenizer(self.model_name)
        if preprocess is None or tokenizer is None or torch_module is None:
            raise ValueError("injected MobileCLIP components must be provided together")
        self._torch = torch_module
        self.batch_size = batch_size
        self._model = model
        self._preprocess = preprocess
        self._tokenizer = tokenizer
        self._model.eval()

    def embed_texts(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        if any(not text.strip() for text in texts):
            raise ValueError("texts must not be blank")
        vectors: list[tuple[float, ...]] = []
        with self._torch.inference_mode():
            for start in range(0, len(texts), self.batch_size):
                tokens = self._tokenizer(list(texts[start : start + self.batch_size]))
                values = self._model.encode_text(tokens)
                values = self._torch.nn.functional.normalize(values, dim=-1)
                vectors.extend(tuple(float(value) for value in row) for row in values.cpu().tolist())
        return tuple(vectors)

    def embed_images(self, image_paths: Sequence[str | Path]) -> tuple[tuple[float, ...], ...]:
        from PIL import Image

        vectors: list[tuple[float, ...]] = []
        with self._torch.inference_mode():
            for start in range(0, len(image_paths), self.batch_size):
                batch_paths = image_paths[start : start + self.batch_size]
                # 统一转换为 RGB，消除灰度图和带透明通道图像的输入差异。
                images = [self._preprocess(Image.open(path).convert("RGB")) for path in batch_paths]
                tensor = self._torch.stack(images)
                values = self._model.encode_image(tensor)
                values = self._torch.nn.functional.normalize(values, dim=-1)
                vectors.extend(tuple(float(value) for value in row) for row in values.cpu().tolist())
        return tuple(vectors)


def _match_input_name(raw_name: str) -> str:
    # TFLite 导出后张量名可能带前后缀，因此按标准字段子串匹配。
    lowered = raw_name.lower()
    for name in ("input_ids", "attention_mask", "token_type_ids"):
        if name in lowered:
            return name
    raise ValueError(f"unrecognized TFLite BERT input: {raw_name}")


def _create_tflite_interpreter(model_path: str):
    # 优先使用轻量 LiteRT；未安装时回退到 TensorFlow Lite。
    try:
        from ai_edge_litert.interpreter import Interpreter
    except ImportError:
        try:
            import tensorflow as tf
            Interpreter = tf.lite.Interpreter
        except ImportError as exc:
            raise RuntimeError("Install ai-edge-litert or tensorflow to run the TFLite backend") from exc
    return Interpreter(model_content=Path(model_path).read_bytes(), num_threads=4)
