DOMAIN_PROFILES = {
    "software": {
        "app", "api", "system", "platform", "backend", "frontend",
        "database", "algorithm", "framework"
    },
    "business": {
        "revenue", "pricing", "market", "customers",
        "startup", "profit", "scaling"
    },
    "social": {
        "community", "rural", "ngo", "education",
        "healthcare", "women", "children", "access"
    },
    "policy": {
        "policy", "governance", "regulation", "public", "law"
    },
    "hardware": {
        "device", "sensor", "mechanical", "embedded",
        "prototype", "manufacturing"
    }
}


def detect_domain_intent(description: str) -> tuple[str, float]:
    text = description.lower()

    scores = {
        domain: sum(1 for k in keywords if k in text)
        for domain, keywords in DOMAIN_PROFILES.items()
    }

    best_domain = max(scores, key=scores.get)
    total = sum(scores.values())

    confidence = scores[best_domain] / total if total else 0.0
    return best_domain, round(confidence, 2)
