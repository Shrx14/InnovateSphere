from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from backend.semantic.embedder import get_embedder


def _import_faiss():
    try:
        import faiss  # type: ignore

        return faiss
    except Exception as exc:  # pragma: no cover - exercised only when dependency missing
        raise RuntimeError(
            "faiss is not available. Install dependency: pip install faiss-cpu"
        ) from exc


@dataclass
class FaissReferenceIndex:
    """Wrapper around a FAISS index with optional metadata sidecar."""

    index: Any
    dimension: int
    metadata: list[dict[str, Any]]

    @classmethod
    def from_texts(
        cls,
        texts: Iterable[str],
        *,
        ids: Iterable[str] | None = None,
        embedder: Any | None = None,
    ) -> "FaissReferenceIndex":
        text_list = [str(t or "") for t in texts]
        if not text_list:
            raise ValueError("Cannot build FAISS index from empty text corpus")

        model = embedder or get_embedder()
        embeddings = np.asarray(
            model.encode(text_list, normalize_embeddings=True),
            dtype="float32",
        )
        if embeddings.ndim != 2:
            raise ValueError("Expected 2D embeddings array")

        faiss = _import_faiss()
        dim = int(embeddings.shape[1])
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)

        id_list = list(ids) if ids is not None else []
        metadata = []
        for i, text in enumerate(text_list):
            metadata.append(
                {
                    "id": id_list[i] if i < len(id_list) else str(i),
                    "text": text,
                }
            )

        return cls(index=index, dimension=dim, metadata=metadata)

    def search_embeddings(self, embedding: np.ndarray, *, k: int = 5) -> tuple[np.ndarray, np.ndarray]:
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)

        embedding = np.asarray(embedding, dtype="float32")
        total = int(getattr(self.index, "ntotal", 0))
        if total == 0:
            return np.zeros((1, 0), dtype="float32"), np.zeros((1, 0), dtype="int64")

        top_k = max(1, min(int(k), total))
        return self.index.search(embedding, top_k)

    def search_text(self, text: str, *, k: int = 5, embedder: Any | None = None) -> list[dict[str, Any]]:
        model = embedder or get_embedder()
        embedding = np.asarray(model.encode([text], normalize_embeddings=True), dtype="float32")
        distances, indices = self.search_embeddings(embedding[0], k=k)

        results = []
        for score, idx in zip(distances[0], indices[0]):
            if int(idx) < 0:
                continue
            payload = self.metadata[int(idx)] if int(idx) < len(self.metadata) else {"id": str(idx)}
            results.append(
                {
                    "score": float(score),
                    "index": int(idx),
                    "id": payload.get("id"),
                    "text": payload.get("text", ""),
                }
            )
        return results

    def save(self, *, index_path: str, metadata_path: str | None = None) -> None:
        faiss = _import_faiss()
        faiss.write_index(self.index, index_path)
        if metadata_path:
            with open(metadata_path, "w", encoding="utf-8") as handle:
                json.dump(self.metadata, handle, ensure_ascii=True)

    @classmethod
    def load(cls, *, index_path: str, metadata_path: str | None = None) -> "FaissReferenceIndex":
        faiss = _import_faiss()
        index = faiss.read_index(index_path)
        dimension = int(getattr(index, "d", 0))

        metadata: list[dict[str, Any]] = []
        if metadata_path:
            with open(metadata_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
                if isinstance(raw, list):
                    metadata = [row for row in raw if isinstance(row, dict)]

        return cls(index=index, dimension=dimension, metadata=metadata)
