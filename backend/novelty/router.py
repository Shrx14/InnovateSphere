from backend.novelty.domain_intent import detect_domain_intent

_SOFTWARE_ANALYZER = None

INTENT_CONFIDENCE_FLOOR = 0.25

# Map the 10 new domains to the software analyst
# All domains now use the software analyzer for consistent, comprehensive novelty analysis
DOMAIN_TO_ENGINE = {
    "AI & Machine Learning": "software",
    "Web & Mobile Development": "software",
    "Data Science & Analytics": "software",
    "Cybersecurity & Privacy": "software",
    "Cloud & DevOps": "software",
    "Blockchain & Web3": "software",
    "IoT & Hardware": "software",
    "Healthcare & Biotech": "software",
    "Education & E-Learning": "software",
    "Business & Productivity Tools": "software",
}


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


def route_engine(description: str, override_domain: str = None):
    """
    Route to the software novelty analysis engine.
    All domains use the comprehensive software analyzer for consistent scoring.
    
    Args:
        description: The idea description text
        override_domain: Optional domain to use instead of auto-detecting from description
        
    Returns (analyzer, domain_name, domain_confidence, problem_class, problem_class_confidence)
    """
    detected_domain, domain_confidence, problem_class, problem_class_confidence = detect_domain_intent(description)

    # Use override domain if provided, otherwise use detected domain
    if override_domain and override_domain in DOMAIN_TO_ENGINE:
        used_domain = override_domain
        # When using override domain, set confidence to 1.0 to indicate explicit selection
        domain_confidence = 1.0
    else:
        used_domain = detected_domain

    # Always use the software analyzer for all domains
    analyzer = _get_software_analyzer()
    if analyzer:
        return analyzer, used_domain, domain_confidence, problem_class, problem_class_confidence
    else:
        # Fallback to generic if software analyzer unavailable
        from backend.novelty.engines.generic import GenericNoveltyEngine
        return GenericNoveltyEngine(), "generic", domain_confidence, problem_class, problem_class_confidence
