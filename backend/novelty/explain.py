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


def generate_detailed_explanation(
    novelty_score: float,
    confidence_tier: str,
    signal_breakdown: dict = None,
    penalties: dict = None,
    source_count: int = 0,
    admin_validated_count: int = 0
):
    """
    Generate comprehensive explanation with signal breakdown and penalty information.
    This provides transparency into HOW a novelty score was calculated.
    """
    
    if signal_breakdown is None:
        signal_breakdown = {}
    if penalties is None:
        penalties = {}
    
    explanation_parts = []
    
    # Main score explanation
    if novelty_score >= 70:
        base_claim = "This idea shows high novelty"
    elif novelty_score >= 40:
        base_claim = "This idea shows moderate novelty"
    else:
        base_claim = "This idea has low novelty"
    
    explanation_parts.append(f"{base_claim} (Score: {novelty_score:.0f}/100)")
    
    # Signal breakdown
    if signal_breakdown:
        explanation_parts.append("\n**Signal Contributions:**")
        total_signals = sum(abs(v) for v in signal_breakdown.values())
        for signal_name, weight in sorted(signal_breakdown.items(), key=lambda x: x[1], reverse=True):
            if total_signals > 0:
                pct = (weight / total_signals * 100) if weight > 0 else -(weight / total_signals * 100)
                if weight > 0:
                    explanation_parts.append(f"  • {signal_name}: +{weight:.1f} (↑{pct:.0f}%)")
                else:
                    explanation_parts.append(f"  • {signal_name}: {weight:.1f} (↓{abs(pct):.0f}%)")
    
    # Confidence explanation (normalize to lowercase for consistent comparison)
    _tier = (confidence_tier or "").strip().lower()
    if _tier == "high":
        reason = f"Based on {source_count} diverse sources"
        if admin_validated_count > 0:
            reason += f" ({admin_validated_count} admin-validated)"
    elif _tier == "medium":
        reason = f"Based on {source_count} sources"
        if admin_validated_count == 0:
            reason += " (no admin validation yet)"
    else:
        reason = f"Limited data: {source_count} sources found"
    
    if confidence_tier:
        explanation_parts.append(f"\n**Confidence: {confidence_tier}**")
        explanation_parts.append(f"  {reason}")
    
    # Penalty breakdown
    if penalties and any(v != 1.0 for v in penalties.values()):
        explanation_parts.append("\n**Adjustments Applied:**")
        
        for penalty_name, multiplier in sorted(penalties.items()):
            if multiplier < 1.0:
                pct_change = int((1 - multiplier) * 100)
                explanation_parts.append(f"  • {penalty_name}: -{pct_change}%")
            elif multiplier > 1.0:
                pct_change = int((multiplier - 1) * 100)
                explanation_parts.append(f"  • {penalty_name}: +{pct_change}%")
    
    # Saturation warning
    if source_count > 15:
        explanation_parts.append("\n⚠️ Note: High saturation detected - many sources cover similar ground")
    
    return {
        "summary": explanation_parts[0],
        "confidence_tier": confidence_tier,
        "confidence_reason": reason if confidence_tier else "",
        "full_narrative": "\n".join(explanation_parts),
        "signals": signal_breakdown,
        "penalties": penalties,
        "source_count": source_count
    }
