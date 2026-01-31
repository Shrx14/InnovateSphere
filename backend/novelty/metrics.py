from typing import List, Dict


def compute_similarity_distribution(
    similarities: List[float], threshold: float = 0.7
) -> Dict[str, float]:
    if not similarities:
        return {
            "mean_similarity": 0.0,
            "variance": 0.0,
            "count_above": 0,
        }

    mean = sum(similarities) / len(similarities)
    variance = sum((s - mean) ** 2 for s in similarities) / len(similarities)
    count_above = sum(1 for s in similarities if s >= threshold)

    return {
        "mean_similarity": round(mean, 3),
        "variance": round(variance, 3),
        "count_above": count_above,
    }
