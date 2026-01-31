def compute_specificity(description: str) -> float:
    words = description.split()
    if len(words) < 5:
        return 0.2

    tech_terms = {
        "api", "database", "algorithm",
        "framework", "protocol", "distributed",
        "system", "pipeline"
    }

    tech_count = sum(1 for w in words if w.lower() in tech_terms)
    length_factor = min(len(words) / 50, 1.0)

    specificity = min(1.0, length_factor + tech_count / 6)
    return round(specificity, 2)
