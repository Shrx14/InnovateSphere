"""
Novelty analysis service - consolidated from services/novelty_service.py
"""
_analyzer = None


def _get_analyzer():
    """Lazy-load analyzer only when needed"""
    global _analyzer
    if _analyzer is None:
        try:
            from backend.novelty.analyzer import NoveltyAnalyzer
            _analyzer = NoveltyAnalyzer()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize NoveltyAnalyzer: {e}. Using fallback.")
            # Return a fallback analyzer that doesn't require transformers
            return None
    return _analyzer


def system_under_load() -> bool:
    # Placeholder — can be CPU, queue depth, etc.
    return False


def analyze_novelty(description: str, domain: str) -> dict:
    """
    Analyze novelty of an idea description within a domain.
    
    Args:
        description: The idea description to analyze
        domain: The domain/category for context
        
    Returns:
        dict containing novelty analysis results
    """
    analyzer = _get_analyzer()
    if analyzer is None:
        # Fallback: return constant score
        return {
            "novelty_score": 65,
            "novelty_level": "Medium",
            "confidence": "Low",
            "explanations": "Fallback analyzer - detailed analysis unavailable",
            "engine": "fallback",
            "trace_id": "fallback_001",
        }
    
    if system_under_load():
        return analyzer.analyze(description, domain)

    return analyzer.analyze(description, domain)
