"""
Novelty explanation generation module.

Provides template-based human-readable explanations for novelty scores.
"""

from typing import List, Dict, Any

def generate_explanation(
    novelty_score: float,
    similarity_stats: Dict[str, float],
    source_count: int,
    avg_popularity_penalty: float,
    sources: List[Dict[str, Any]]
) -> List[str]:
    """
    Generate structured explanation for novelty analysis.

    Args:
        novelty_score: Final novelty score (0-100)
        similarity_stats: Similarity distribution statistics
        source_count: Number of sources analyzed
        avg_popularity_penalty: Average popularity penalty
        sources: List of similar sources

    Returns:
        List of explanation strings
    """
    explanations = []

    # Overall novelty statement
    level = "high" if novelty_score >= 70 else "medium" if novelty_score >= 40 else "low"
    explanations.append(f"Overall novelty is {level} ({novelty_score:.1f}/100).")

    # Similarity distribution
    mean_sim = similarity_stats['mean_similarity']
    count_above = similarity_stats['count_above_threshold']

    if mean_sim < 0.3:
        sim_desc = "low"
    elif mean_sim < 0.6:
        sim_desc = "moderate"
    else:
        sim_desc = "high"

    explanations.append(f"Average similarity to existing sources is {sim_desc} ({mean_sim:.2f}).")

    if count_above > 0:
        explanations.append(f"Found {count_above} sources with high similarity (≥0.7).")
    else:
        explanations.append("No sources with very high similarity found.")

    # Source count and saturation
    if source_count == 0:
        explanations.append("No similar sources found in the analysis.")
    elif source_count == 1:
        explanations.append("Only 1 similar source found.")
    else:
        explanations.append(f"Analysis considered {source_count} similar sources.")

    # Popularity impact
    if avg_popularity_penalty > 0.5:
        explanations.append("Many similar ideas are popular, reducing novelty.")
    elif avg_popularity_penalty > 0.2:
        explanations.append("Some similar ideas are moderately popular.")
    else:
        explanations.append("Similar ideas are relatively obscure.")

    # Key insights
    if novelty_score >= 70:
        explanations.append("This appears to be a fresh concept with limited overlap.")
    elif novelty_score >= 40:
        explanations.append("This has moderate overlap with existing work.")
    else:
        explanations.append("This concept has significant overlap with existing sources.")

    return explanations
