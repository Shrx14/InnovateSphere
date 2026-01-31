def compute_bonuses(description: str, domain: str) -> float:
    text = description.lower()
    bonus = 0.0

    if any(t in text for t in ["ai", "ml", "blockchain", "quantum", "crdt"]):
        bonus += 6.0

    if any(t in text for t in ["distributed", "microservices", "serverless"]):
        bonus += 4.0

    if any(t in text for t in ["hybrid", "cross-domain", "integration"]):
        bonus += 3.0

    return bonus
