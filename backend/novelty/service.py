"""
Novelty analysis service - consolidated from services/novelty_service.py
"""
_analyzer = None


def _get_analyzer():
    """Lazy-load analyzer only when needed"""
    global _analyzer
    if _analyzer is None:
        from backend.novelty.analyzer import NoveltyAnalyzer
        _analyzer = NoveltyAnalyzer()
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
        
    Raises:
        RuntimeError: If novelty analyzer cannot be initialized
    """
    analyzer = _get_analyzer()
    
    if system_under_load():
        return analyzer.analyze(description, domain)

    return analyzer.analyze(description, domain)
