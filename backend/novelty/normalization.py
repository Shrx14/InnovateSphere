ENGINE_CAPS = {
    "software": 100,
    "business": 85,
    "social": 80,
    "generic": 60,
}


def normalize_score(score: float, engine: str) -> float:
    cap = ENGINE_CAPS.get(engine, 70)
    scaled = min(score, cap) * (100 / cap)
    return round(scaled, 1)


def determine_level(score: float) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"
