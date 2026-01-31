from backend.novelty.analyzer import NoveltyAnalyzer


_analyzer = NoveltyAnalyzer()


def system_under_load() -> bool:
    # Placeholder — can be CPU, queue depth, etc.
    return False


def analyze_novelty(description: str, domain: str) -> dict:
    if system_under_load():
        return _analyzer.analyze(description, domain)

    return _analyzer.analyze(description, domain)
