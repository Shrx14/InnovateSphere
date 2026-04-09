import logging
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.core.config import Config

_embedder = None

logger = logging.getLogger(__name__)


class _OnnxMiniLMEmbedder:
    def __init__(self, model_path: str, tokenizer_name: str):
        from optimum.onnxruntime import ORTModelForFeatureExtraction
        from transformers import AutoTokenizer

        self._model = ORTModelForFeatureExtraction.from_pretrained(model_path)
        self._tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

    def encode(self, texts, normalize_embeddings: bool = True):
        if isinstance(texts, str):
            texts = [texts]

        encoded = self._tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="np",
        )
        output = self._model(**encoded)
        hidden = output.last_hidden_state

        # Mean pooling with attention mask for stable sentence embeddings.
        mask = encoded["attention_mask"][..., None]
        pooled = (hidden * mask).sum(axis=1) / np.clip(mask.sum(axis=1), 1e-12, None)

        if normalize_embeddings:
            pooled = pooled / np.clip(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12, None)

        return pooled

def get_embedder():
    global _embedder
    if _embedder is None:
        backend = getattr(Config, "EMBEDDING_BACKEND", "auto").strip().lower()

        try_onnx = backend in {"auto", "onnx"}
        if try_onnx and getattr(Config, "EMBEDDING_ONNX_MODEL_PATH", ""):
            try:
                _embedder = _OnnxMiniLMEmbedder(
                    Config.EMBEDDING_ONNX_MODEL_PATH,
                    Config.EMBEDDING_ONNX_TOKENIZER,
                )
                logger.info("Using ONNX embedding backend from %s", Config.EMBEDDING_ONNX_MODEL_PATH)
                return _embedder
            except Exception as exc:
                logger.warning("ONNX embedder unavailable (%s); falling back to sentence-transformers", exc)

        _embedder = SentenceTransformer(Config.EMBEDDING_MODEL)
    return _embedder

class Embedder:
    def __init__(self):
        self._embedder = get_embedder()

    def embed_texts(self, texts: List[str]):
        return self._embedder.encode(texts, normalize_embeddings=True)

    # Backwards-compatible alias used by other modules
    def encode(self, texts: List[str], normalize_embeddings: bool = True):
        return self._embedder.encode(texts, normalize_embeddings=normalize_embeddings)
