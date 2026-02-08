from backend.novelty.config import DOMAIN_NOVELTY_WEIGHT
from backend.novelty.utils.observability import check_stability, trace_analysis, record_telemetry

from backend.novelty.scoring.base import compute_base_score
from backend.novelty.scoring.bonuses import compute_bonuses
from backend.novelty.scoring.blending import blend
from backend.novelty.scoring.penalties import compute_saturation_penalty, compute_admin_penalty

from backend.core.db import db
from backend.core.models import ProjectIdea, Domain


from backend.novelty.utils.signals import compute_similarity_stats, compute_specificity_signal, compute_temporal_signal
from backend.novelty.normalization import determine_level
from backend.novelty.explain import generate_explanation

from backend.retrieval.cached_retrieval import cached_retrieve_sources
from backend.semantic.cached_embedder import CachedEmbedder


class NoveltyAnalyzer:
    def __init__(self):
        self.embedder = CachedEmbedder()

    def _admin_stats(self, domain_name: str):
        domain = Domain.query.filter_by(name=domain_name).first()
        if not domain:
            return 0.0, 0.0

        ideas = ProjectIdea.query.filter_by(domain_id=domain.id).all()
        if not ideas:
            return 0.0, 0.0

        total = len(ideas)
        rejected = sum(
            1 for i in ideas
            if i.admin_verdict and i.admin_verdict.verdict == "rejected"
        )
        validated = sum(
            1 for i in ideas
            if i.admin_verdict and i.admin_verdict.verdict == "validated"
        )

        return rejected / total, validated / total

    def _compute_hitl_penalty(self, sources: list) -> float:
        """
        Compute HITL penalty based on aggregate signals over similar idea set.
        Similar idea set: ideas that share sources with the retrieved sources.
        """
        if not sources:
            return 0.0

        source_urls = {s.get("url") for s in sources if s.get("url")}
        if not source_urls:
            return 0.0

        # Find ideas that have any of these URLs as sources
        from backend.core.models import IdeaSource

        similar_idea_ids = [
            s.idea_id
            for s in IdeaSource.query
                .filter(IdeaSource.url.in_(source_urls))
                .distinct()
                .all()
        ]

        if not similar_idea_ids:
            return 0.0

        # Get verdicts for these ideas
        verdicts = [
            idea.admin_verdict
            for idea in ProjectIdea.query.filter(ProjectIdea.id.in_(similar_idea_ids)).all()
        ]

        total = len(verdicts)
        rejected = sum(1 for v in verdicts if v and v.verdict == "rejected")
        downgraded = sum(1 for v in verdicts if v and v.verdict == "downgraded")
        validated = sum(1 for v in verdicts if v and v.verdict == "validated")

        rejection_rate = rejected / total if total > 0 else 0.0
        downgrade_rate = downgraded / total if total > 0 else 0.0

        # Get avg quality score
        quality_scores = [
            i.quality_score for i in ProjectIdea.query.filter(ProjectIdea.id.in_(similar_idea_ids)).all()
        ]
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 50.0

        # Compute bounded penalty term
        penalty = 0.0
        penalty -= rejection_rate * 20  # up to -20 for high rejection
        penalty -= downgrade_rate * 10  # up to -10 for high downgrade
        penalty += (avg_quality_score - 50) * 0.1  # small bonus/penalty based on quality

        return max(-30, min(10, penalty))  # bound between -30 and 10

    def analyze(self, description: str, domain: str):
        sources = cached_retrieve_sources(
            query=description,
            domain=domain,
            limit=20,
            semantic_filter=False,
        ).get("sources", [])

        sim_stats = compute_similarity_stats(description, sources, self.embedder)
        specificity = compute_specificity_signal(description)
        temporal = compute_temporal_signal(sources)
        saturation = compute_saturation_penalty(len(sources))

        signals = {
            "similarity": sim_stats["mean_similarity"],
            "specificity": specificity,
            "temporal": temporal["recency_score"],
            "saturation": saturation,
        }

        base = compute_base_score(signals)
        bonus = compute_bonuses(description, domain)
        hitl_penalty = self._compute_hitl_penalty(sources)
        score = blend(base * 0.9, base + bonus + hitl_penalty)

        weighted = score * DOMAIN_NOVELTY_WEIGHT.get(domain.lower(), 1.0)
        stabilized = check_stability(description + domain, weighted, "Medium")

        explanations = generate_explanation(
            novelty_score=stabilized,
            similarity_stats=sim_stats,
            source_count=len(sources),
            avg_popularity_penalty=saturation,
            sources=sources,
        )

        record_telemetry("novelty.software.score", stabilized)
        trace_id = trace_analysis({"score": stabilized, "sources": len(sources)})

        return {
            "novelty_score": round(stabilized, 1),
            "novelty_level": determine_level(stabilized),
            "confidence": "High" if len(sources) >= 8 else "Medium",
            "explanations": explanations,
            "engine": "software",
            "trace_id": trace_id,
            "debug": {
                "retrieved_sources": len(sources),
                "similarity_variance": sim_stats.get("variance", 0.5),
            },
        }
