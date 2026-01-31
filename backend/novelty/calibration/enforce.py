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
