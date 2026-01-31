import numpy as np
from backend.semantic.embedder import Embedder

def _cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def filter_by_semantic_similarity(query_text, sources, threshold):
    query_emb = Embedder.embed_texts([query_text])[0]

    texts = [s.get("summary", "") or "" for s in sources]
    source_embs = Embedder.embed_texts(texts)

    filtered = []
    for src, emb in zip(sources, source_embs):
        sim = _cosine_similarity(query_emb, emb)
        if sim >= threshold:
            src["similarity_score"] = float(sim)
            filtered.append(src)

    return filtered
