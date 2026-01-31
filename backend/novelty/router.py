from backend.novelty.domain_intent import detect_domain_intent
from backend.novelty.analyzer import NoveltyAnalyzer

_SOFTWARE_ANALYZER = NoveltyAnalyzer()

INTENT_CONFIDENCE_FLOOR = 0.25


def route_engine(description: str):
    intent, confidence = detect_domain_intent(description)

    if confidence < INTENT_CONFIDENCE_FLOOR:
        from backend.novelty.engines.generic import GenericNoveltyEngine
        return GenericNoveltyEngine(), "generic", confidence

    if intent == "software":
        return _SOFTWARE_ANALYZER, intent, confidence

    if intent == "business":
        from backend.novelty.engines.business import BusinessNoveltyEngine
        return BusinessNoveltyEngine(), intent, confidence

    if intent == "social":
        from backend.novelty.engines.social import SocialNoveltyEngine
        return SocialNoveltyEngine(), intent, confidence

    from backend.novelty.engines.generic import GenericNoveltyEngine
    return GenericNoveltyEngine(), "generic", confidence
