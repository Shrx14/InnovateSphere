import numpy as np
import logging
from backend.semantic.embedder import Embedder

def _cosine_similarity(a, b):
    den = np.linalg.norm(a) * np.linalg.norm(b)
    sim = np.dot(a, b) / den if den else 0.0
    return sim

def filter_by_semantic_similarity(query_text, sources, threshold):
    try:
        query_emb = Embedder.embed_texts([query_text])[0]

        texts = [s.get("summary", "") or "" for s in sources]
        source_embs = Embedder.embed_texts(texts)

        for src, emb in zip(sources, source_embs):
            sim = _cosine_similarity(query_emb, emb)
            src["similarity_score"] = float(sim)

        filtered = [src for src in sources if src["similarity_score"] >= threshold]
        return filtered
    except Exception as e:
        logging.warning("Semantic filter skipped: %s", str(e))
        return sources  # Return unfiltered sources as fallback
