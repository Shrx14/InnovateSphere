import numpy as np
from backend.novelty.metrics import compute_similarity_distribution

def compute_similarities(description: str, sources: list, embedder) -> list:
    if not sources:
        return []

    texts = [s.get("summary") or s.get("title", "") for s in sources]
    vectors = embedder.encode(texts, normalize_embeddings=True)
    query_vec = embedder.encode([description], normalize_embeddings=True)[0]

    return [float(np.dot(query_vec, v)) for v in vectors]


def compute_similarity_stats(description: str, sources: list, embedder) -> dict:
    similarities = compute_similarities(description, sources, embedder)
    return compute_similarity_distribution(similarities)
