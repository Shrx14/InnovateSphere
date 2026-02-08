# backend/semantic/cached_embedder.py

import hashlib
from functools import lru_cache
from typing import List

from backend.semantic.embedder import Embedder


class CachedEmbedder:
    """
    Cached embedding wrapper.
    Safe to use across requests (in-memory).
    """

    def __init__(self):
        self._embedder = Embedder()

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.strip().lower().encode()).hexdigest()

    @lru_cache(maxsize=5000)
    def _embed_single(self, text: str):
        return self._embedder.embed_texts([text])[0]

    def embed_texts(self, texts: List[str]):
        return [self._embed_single(t) for t in texts]

    # Backwards-compatible alias: allow callers to use `encode()` like SentenceTransformer
    def encode(self, texts: List[str], normalize_embeddings: bool = True):
        # ignore normalize_embeddings here because underlying embedder normalizes
        return self.embed_texts(texts)
