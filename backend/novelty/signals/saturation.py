def compute_saturation(source_count: int, max_sources: int = 15) -> float:
    """
    Compute saturation score based on number of similar sources.

    Args:
        source_count: Number of sources
        max_sources: Max sources to consider

    Returns:
        Saturation score (0-1, higher = more saturated)
    """
    return min(source_count / max_sources, 1.0)
