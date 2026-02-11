import numpy as np
import logging
from backend.semantic.cached_embedder import CachedEmbedder


def _cosine_similarity(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    den = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / den) if den else 0.0


def filter_by_semantic_similarity(query_text, sources, threshold):
    """
    Filter sources by semantic similarity to the query using cached embeddings.

    Returns the subset of `sources` whose similarity_score >= threshold and
    populates `similarity_score` on each source.
    """
    try:
        embedder = CachedEmbedder()

        query_emb = embedder.embed_texts([query_text])[0]

        texts = [s.get("summary") or s.get("title") or "" for s in sources]
        source_embs = embedder.embed_texts(texts)

        for src, emb in zip(sources, source_embs):
            sim = _cosine_similarity(query_emb, emb)
            src["similarity_score"] = float(sim)

        filtered = [src for src in sources if src.get("similarity_score", 0.0) >= threshold]
        return filtered
    except Exception as e:
        logging.warning("Semantic filter skipped: %s", str(e))
        return sources
