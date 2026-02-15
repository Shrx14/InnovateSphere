from backend.novelty.normalization import determine_level

class GenericNoveltyEngine:
    def analyze(self, description: str, domain: str, problem_class: str = "general"):
        length_factor = min(len(description.split()) / 50, 1.0)
        score = 15 + length_factor * 25

        return {
            "novelty_score": round(score, 1),
            "novelty_level": determine_level(score),
            "confidence": "Low",
            "engine": "generic",
            "debug": {
                "retrieved_sources": 0,
                "similarity_variance": 0.5,
            },
        }
