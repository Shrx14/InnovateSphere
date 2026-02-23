from typing import List, Dict, Optional


def compute_similarity_distribution(
    similarities: List[float], threshold: float = 0.7, domain: Optional[str] = None
) -> Dict[str, float]:
    # Use domain-specific threshold when available
    if domain:
        from backend.novelty.config import SIMILARITY_THRESHOLDS
        threshold = SIMILARITY_THRESHOLDS.get(
            domain, SIMILARITY_THRESHOLDS.get(domain.lower(), threshold)
        )
    if not similarities:
        return {
            "mean_similarity": 0.0,
            "variance": 0.0,
            "count_above": 0,
            # backward-compatible key expected by other modules
            "count_above_threshold": 0,
        }

    mean = sum(similarities) / len(similarities)
    variance = sum((s - mean) ** 2 for s in similarities) / len(similarities)
    count_above = sum(1 for s in similarities if s >= threshold)

    return {
        "mean_similarity": round(mean, 3),
        "variance": round(variance, 3),
        "count_above": count_above,
        # provide both keys for compatibility
        "count_above_threshold": count_above,
    }
