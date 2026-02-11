def compute_bonuses(description: str, domain: str, source_count: int = 0) -> float:
    """
    Only award bonuses when evidence (sources) exist.
    Zero sources = zero bonuses, regardless of keywords.
    """
    text = description.lower()
    bonus = 0.0
    
    # CRITICAL: No bonuses if no sources found
    if source_count == 0:
        return 0.0

    if any(t in text for t in ["ai", "ml", "blockchain", "quantum", "crdt"]):
        bonus += 6.0

    if any(t in text for t in ["distributed", "microservices", "serverless"]):
        bonus += 4.0

    if any(t in text for t in ["hybrid", "cross-domain", "integration"]):
        bonus += 3.0

    return bonus
