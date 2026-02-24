"""DEPRECATED: This engine is not used in production.
All domains route through NoveltyAnalyzer (software engine).
Kept for reference only — safe to remove."""
import warnings
warnings.warn("SocialNoveltyEngine is deprecated and unused", DeprecationWarning, stacklevel=2)

class SocialNoveltyEngine:
    def analyze(self, description: str, domain: str, problem_class: str = "general"):
        text = description.lower()

        score = 30
        signals = 0

        if any(k in text for k in ["rural", "remote", "underserved"]):
            score += 20
            signals += 1

        if any(k in text for k in ["community", "women", "children"]):
            score += 15
            signals += 1

        if any(k in text for k in ["pilot", "first of its kind", "new model"]):
            score += 15
            signals += 1

        score = min(score, 80)

        novelty_level = (
            "High" if score >= 70 else
            "Medium" if score >= 40 else
            "Low"
        )

        return {
            "novelty_score": score,
            "novelty_level": novelty_level,
            "confidence": "High" if signals >= 2 else "Medium",
            "engine": "social",
            "debug": {
                "retrieved_sources": 0,
                "similarity_variance": 0.5,
            },
        }
