"""DEPRECATED: This engine is not used in production.
All domains route through NoveltyAnalyzer (software engine).
Kept for reference only — safe to remove."""
import warnings
warnings.warn("BusinessNoveltyEngine is deprecated and unused", DeprecationWarning, stacklevel=2)

from backend.novelty.normalization import determine_level

class BusinessNoveltyEngine:
    def analyze(self, description: str, domain: str, problem_class: str = "general"):
        text = description.lower()

        score = 30
        signals = 0

        if any(k in text for k in ["pricing", "subscription", "freemium"]):
            score += 15
            signals += 1

        if any(k in text for k in ["underserved", "niche", "long tail"]):
            score += 20
            signals += 1

        if any(k in text for k in ["marketplace", "two-sided", "platform"]):
            score += 15
            signals += 1

        score = min(score, 85)

        return {
            "novelty_score": score,
            "novelty_level": determine_level(score),
            "confidence": "High" if signals >= 2 else "Medium",
            "engine": "business",
            "debug": {
                "retrieved_sources": 0,
                "similarity_variance": 0.5,
            },
        }
