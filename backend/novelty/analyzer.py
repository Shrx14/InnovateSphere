import logging

from backend.novelty.config import DOMAIN_NOVELTY_WEIGHT
from backend.novelty.utils.observability import check_stability, trace_analysis, record_telemetry

from backend.novelty.scoring.base import compute_base_score
from backend.novelty.scoring.bonuses import compute_bonuses
from backend.novelty.scoring.blending import blend
from backend.novelty.scoring.penalties import compute_saturation_penalty, compute_admin_penalty

from backend.core.db import db
from backend.core.models import ProjectIdea, Domain


from backend.novelty.utils.signals import compute_similarity_stats, compute_specificity_signal, compute_temporal_signal
from backend.novelty.normalization import determine_level, normalize_score
from backend.novelty.explain import generate_explanation

from backend.retrieval.cached_retrieval import cached_retrieve_sources
from backend.semantic.cached_embedder import CachedEmbedder

logger = logging.getLogger(__name__)


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

        # Validate we have sources for novelty comparison baseline
        if not sources:
            logger.warning(
                "[Novelty] No sources found for domain=%s | Unable to assess novelty without reference data",
                domain
            )
            # Return baseline score with low confidence when no sources available
            return {
                "novelty_score": 50.0,  # Neutral score when no baseline exists
                "novelty_level": determine_level(50.0),
                "confidence": "Low",
                "explanations": [
                    "Unable to assess novelty: no reference sources found in this domain.",
                    "Try refining your query or check if this is an emerging domain with limited public repositories.",
                ],
                "insights": {
                    "summary": "Insufficient domain data for novelty assessment",
                    "details": [],
                },
                "sources": [],
                "engine": "software",
                "trace_id": None,
                "debug": {
                    "retrieved_sources": 0,
                    "similarity_variance": 0.0,
                },
            }

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

        # Helper to truncate long texts for summaries
        def _truncate(text: str, n: int = 400) -> str:
            if not text:
                return ""
            return text if len(text) <= n else text[: n - 1] + "…"

        # Sanitize sources for public API consumption (use for bonuses count)
        sanitized_sources = []
        for s in sources[:20]:
            sanitized_sources.append({
                "title": s.get("title") or s.get("name") or (s.get("url") or ""),
                "url": s.get("url"),
                "source_type": s.get("source_type"),
                "summary": _truncate(s.get("summary") or s.get("snippet") or s.get("description") or ""),
                "confidence": s.get("confidence"),
            })

        # Compute bonuses based on the final sanitized source count
        bonus = compute_bonuses(description, domain, source_count=len(sanitized_sources))
        hitl_penalty = self._compute_hitl_penalty(sources)
        score = blend(base * 0.9, base + bonus + hitl_penalty)

        weighted = score * DOMAIN_NOVELTY_WEIGHT.get(domain.lower(), 1.0)
        stabilized = check_stability(description + domain, weighted, "Medium")

        # Normalize score to engine caps before mapping to level
        normalized = normalize_score(stabilized, "software")

        explanations = generate_explanation(
            novelty_score=stabilized,
            similarity_stats=sim_stats,
            source_count=len(sanitized_sources),
            avg_popularity_penalty=saturation,
            sources=sources,
        )

        record_telemetry("novelty.software.score", stabilized)

        # Expanded trace payload for debugging
        trace_payload = {
            "score_raw": round(stabilized, 1),
            "score_normalized": normalized,
            "base": round(base, 2),
            "bonus": round(bonus, 2),
            "hitl_penalty": round(hitl_penalty, 2),
            "weighted": round(weighted, 2),
            "signals": signals,
            "sources_count": len(sanitized_sources),
            "confidence_hint": "High" if len(sanitized_sources) >= 8 else "Medium",
        }
        trace_id = trace_analysis(trace_payload)

        # Build a structured insights object from explanations
        insights = {
            "summary": _truncate(explanations[0]) if explanations else "",
            "details": [
                _truncate(e) for e in explanations[1:5]
            ],
        }

        return {
            "novelty_score": normalized,
            "novelty_level": determine_level(normalized),
            "confidence": "High" if len(sanitized_sources) >= 8 else "Medium",
            "explanations": explanations,
            "insights": insights,
            "sources": sanitized_sources,
            "engine": "software",
            "trace_id": trace_id,
            "debug": {
                "retrieved_sources": len(sources),
                "sanitized_sources": len(sanitized_sources),
                "similarity_variance": sim_stats.get("variance", 0.5),
            },
        }
