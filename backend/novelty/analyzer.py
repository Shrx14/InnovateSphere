from backend.novelty.config import DOMAIN_NOVELTY_WEIGHT
from backend.novelty.observability.stability import stabilize_score
from backend.novelty.observability.trace import log_trace
from backend.novelty.observability.telemetry import record

from backend.novelty.scoring.base import compute_base_score
from backend.novelty.scoring.bonuses import compute_bonuses
from backend.novelty.scoring.blending import blend
from backend.novelty.scoring.penalties import compute_saturation_penalty

from backend.novelty.signals.similarity import compute_similarity_stats
from backend.novelty.signals.specificity import compute_specificity
from backend.novelty.signals.temporal import compute_temporal_signals
from backend.novelty.normalization import determine_level

from backend.retrieval.cached_retrieval import cached_retrieve_sources
from backend.semantic.cached_embedder import CachedEmbedder


class NoveltyAnalyzer:
    def __init__(self):
        self.embedder = CachedEmbedder()

    def analyze(self, description: str, domain: str):
        sources = cached_retrieve_sources(
            query=description,
            domain=domain,
            limit=20,
            semantic_filter=False,
        ).get("sources", [])

        sim_stats = compute_similarity_stats(description, sources, self.embedder)
        specificity = compute_specificity(description)
        temporal = compute_temporal_signals(sources)
        saturation = compute_saturation_penalty(len(sources))

        signals = {
            "similarity": sim_stats["mean_similarity"],
            "specificity": specificity,
            "temporal": temporal["recency_score"],
            "saturation": saturation,
        }

        base = compute_base_score(signals)
        bonus = compute_bonuses(description, domain)
        score = blend(base * 0.9, base + bonus)

        weighted = score * DOMAIN_NOVELTY_WEIGHT.get(domain.lower(), 1.0)
        stabilized = stabilize_score(description + domain, weighted, "Medium")

        record("novelty.software.score", stabilized)
        trace_id = log_trace({"score": stabilized, "sources": len(sources)})

        return {
            "novelty_score": round(stabilized, 1),
            "novelty_level": determine_level(stabilized),
            "confidence": "High" if len(sources) >= 8 else "Medium",
            "engine": "software",
            "trace_id": trace_id,
            "debug": {
                "retrieved_sources": len(sources),
                "similarity_variance": sim_stats.get("variance", 0.5),
            },
        }
