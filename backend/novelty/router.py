from backend.novelty.domain_intent import detect_domain_intent

_SOFTWARE_ANALYZER = None

INTENT_CONFIDENCE_FLOOR = 0.25


def _get_software_analyzer():
    """Lazy-load software analyzer only when needed"""
    global _SOFTWARE_ANALYZER
    if _SOFTWARE_ANALYZER is None:
        try:
            from backend.novelty.analyzer import NoveltyAnalyzer
            _SOFTWARE_ANALYZER = NoveltyAnalyzer()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load software analyzer: {e}. Using generic fallback.")
            # Return None - caller will handle
            return None
    return _SOFTWARE_ANALYZER


def route_engine(description: str):
    intent, confidence = detect_domain_intent(description)

    if confidence < INTENT_CONFIDENCE_FLOOR:
        from backend.novelty.engines.generic import GenericNoveltyEngine
        return GenericNoveltyEngine(), "generic", confidence

    if intent == "software":
        analyzer = _get_software_analyzer()
        if analyzer:
            return analyzer, intent, confidence
        else:
            # Fallback to generic if software analyzer unavailable
            from backend.novelty.engines.generic import GenericNoveltyEngine
            return GenericNoveltyEngine(), "generic", confidence

    if intent == "business":
        from backend.novelty.engines.business import BusinessNoveltyEngine
        return BusinessNoveltyEngine(), intent, confidence

    if intent == "social":
        from backend.novelty.engines.social import SocialNoveltyEngine
        return SocialNoveltyEngine(), intent, confidence

    from backend.novelty.engines.generic import GenericNoveltyEngine
    return GenericNoveltyEngine(), "generic", confidence
