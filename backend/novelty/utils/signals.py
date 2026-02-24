"""
Signal computation utilities for novelty analysis.
"""
import numpy as np
from datetime import datetime, timedelta
from backend.novelty.metrics import compute_similarity_distribution


def compute_similarity_signal(description: str, sources: list, embedder) -> list:
    """
    Compute similarity scores between description and sources.
    """
    if not sources:
        return []

    texts = [s.get("summary") or s.get("title", "") for s in sources]
    if not any(texts):
        return []

    vectors = embedder.encode(texts, normalize_embeddings=True)
    query_vec = embedder.encode([description], normalize_embeddings=True)[0]

    return [float(np.dot(query_vec, v)) for v in vectors]


def compute_similarity_stats(description: str, sources: list, embedder, domain: str = "generic") -> dict:
    """
    Compute similarity statistics for sources.
    """
    similarities = compute_similarity_signal(description, sources, embedder)
    return compute_similarity_distribution(similarities, domain=domain)


def compute_specificity_signal(description: str) -> float:
    """
    Compute specificity score based on technical terms and length.
    """
    words = description.split()
    if len(words) < 5:
        return 0.2

    from backend.novelty.config import TECH_TERMS
    tech_terms = TECH_TERMS

    tech_count = sum(1 for w in words if w.lower() in tech_terms)
    length_factor = min(len(words) / 50, 1.0)

    specificity = min(1.0, length_factor + tech_count / 6)
    return round(specificity, 2)


def compute_temporal_signal(sources: list) -> dict:
    """
    Compute temporal signals (recency and activity) from sources.
    """
    if not sources:
        return {"recency_score": 0.5, "activity_score": 0.5}

    now = datetime.utcnow()
    recent_threshold = now - timedelta(days=365)

    recent = 0
    activity = 0.0

    for s in sources:
        date = s.get("published_date")
        if not date:
            continue
        try:
            pub = datetime.fromisoformat(date.replace("Z", "+00:00"))
            if pub > recent_threshold:
                recent += 1
            age_days = (now - pub).days
            activity += max(0, 1 - age_days / 365)
        except Exception:
            continue

    n = max(len(sources), 1)
    return {
        "recency_score": round(recent / n, 2),
        "activity_score": round(activity / n, 2)
    }
