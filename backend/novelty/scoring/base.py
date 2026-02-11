def compute_base_score(signals: dict) -> float:
    return (
        (1 - signals["similarity"]) * 40 +
        signals["specificity"] * 30 +
        (1 - signals["saturation"]) * 20 +
        signals["temporal"] * 10
    )
