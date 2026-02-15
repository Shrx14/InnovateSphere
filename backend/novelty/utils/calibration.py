"""
Evidence-based calibration and constraint enforcement for novelty scores.
"""

def enforce_evidence_constraints(
    *,
    score: float,
    level: str,
    confidence: str,
    evidence_score: float
) -> dict:
    """
    Enforces binding constraints between evidence and outcome.
    This is NOT cosmetic — it caps scores and levels.
    """

    # Speculative zone
    if evidence_score < 0.4:
        return {
            "novelty_score": min(score, 55),
            "novelty_level": "Speculative",
            "confidence": "Low",
        }

    # Medium evidence: cannot claim High novelty
    if evidence_score < 0.65 and level == "High":
        return {
            "novelty_score": min(score, 69),
            "novelty_level": "Medium",
            "confidence": confidence if confidence != "High" else "Medium",
        }

    # Strong evidence → allow full expression
    return {
        "novelty_score": score,
        "novelty_level": level,
        "confidence": confidence,
    }


def compute_evidence_score(debug: dict, intent_confidence: float, sources: list = None) -> float:
    """
    Evidence score ∈ [0,1], based ONLY on existing metadata and source relevance tiers.
    No embeddings. No retrieval. No heuristics.
    
    Args:
        debug: Debug dict with retrieved_sources count
        intent_confidence: Domain/problem-class confidence
        sources: Optional list of sources with relevance_tier field
        
    Returns:
        Evidence score 0-1
    """
    source_count = debug.get("retrieved_sources", 0)
    variance = (
        debug.get("similarity_variance")
        or debug.get("variance")
        or 0.5
    )

    # If sources provided, only count "supporting" tier in evidence
    if sources:
        supporting_count = sum(1 for s in sources if s.get("relevance_tier") == "supporting")
        contextual_count = sum(1 for s in sources if s.get("relevance_tier") == "contextual")
        total_count = len(sources)
        
        # Supporting sources score at 100%, contextual at 50%
        weighted_source_count = supporting_count + (contextual_count * 0.5)
        source_score = min(weighted_source_count / 8, 1.0)
    else:
        if source_count == 0:
            source_score = 0.2  # minimal epistemic credit
        else:
            source_score = min(source_count / 8, 1.0)
    
    variance_score = 1 - min(variance, 1.0)

    evidence = (
        0.4 * source_score +
        0.3 * variance_score +
        0.3 * intent_confidence
    )
    return round(evidence, 2)


def apply_evidence_constraints(result: dict, evidence: float, sources: list = None) -> dict:
    """
    Enforce HARD caps. This must modify score, level, confidence.
    Cosmetic relabeling is NOT acceptable.
    
    Also penalize if arXiv evidence came from "domain_only" fallback.
    """

    score = result.get("novelty_score", 0)
    level = result.get("novelty_level", "Low")
    confidence = result.get("confidence", "Low")

    speculative = False
    evidence_notes = []

    # Check if arXiv sources relied on domain-only fallback
    if sources:
        arxiv_sources = [s for s in sources if s.get("source_type") == "arxiv"]
        domain_only_count = sum(1 for s in arxiv_sources 
                               if s.get("metadata", {}).get("query_variation_quality") == "domain_only")
        
        if arxiv_sources and domain_only_count > len(arxiv_sources) * 0.5:
            # More than 50% of arXiv sources came from domain-only fallback
            evidence_penalty = 0.2
            evidence = max(0, evidence - evidence_penalty)
            evidence_notes.append("Academic evidence based on domain keywords only; problem-type match is weak.")
            
            # Also reduce confidence if relying on weak arXiv evidence
            if confidence == "High":
                confidence = "Medium"

    if evidence < 0.20:
        score = min(score, 30)
        level = "Low"
        confidence = "Low"
        speculative = True

    elif evidence < 0.35:
        score = min(score, 45)
        level = "Medium"
        confidence = "Low"
        speculative = True

    update_dict = {
        "novelty_score": round(score, 1),
        "novelty_level": level,
        "confidence": confidence,
        "speculative": speculative,
        "evidence_score": evidence
    }

    if speculative:
        evidence_notes.insert(0, "Insufficient comparable data; score is capped for safety.")
    
    if evidence_notes:
        update_dict["evidence_note"] = " ".join(evidence_notes)

    result.update(update_dict)

    return result
