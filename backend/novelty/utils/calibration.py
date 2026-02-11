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


def compute_evidence_score(debug: dict, intent_confidence: float) -> float:
    """
    Evidence score ∈ [0,1], based ONLY on existing metadata.
    No embeddings. No retrieval. No heuristics.
    """
    sources = debug.get("retrieved_sources", 0)
    variance = (
        debug.get("similarity_variance")
        or debug.get("variance")
        or 0.5
    )

    if sources == 0:
        source_score = 0.2  # minimal epistemic credit
    else:
        source_score = min(sources / 8, 1.0)
    variance_score = 1 - min(variance, 1.0)

    evidence = (
        0.4 * source_score +
        0.3 * variance_score +
        0.3 * intent_confidence
    )
    return round(evidence, 2)


def apply_evidence_constraints(result: dict, evidence: float) -> dict:
    """
    Enforce HARD caps. This must modify score, level, confidence.
    Cosmetic relabeling is NOT acceptable.
    """

    score = result.get("novelty_score", 0)
    level = result.get("novelty_level", "Low")
    confidence = result.get("confidence", "Low")

    speculative = False

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
        update_dict["evidence_note"] = "Insufficient comparable data; score is capped for safety."

    result.update(update_dict)

    return result
