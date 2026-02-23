import logging

from backend.novelty.config import DOMAIN_NOVELTY_WEIGHT, SIMILARITY_THRESHOLDS, DOMAIN_MATURITY, COMMODITY_PATTERNS
from backend.novelty.utils.observability import check_stability, trace_analysis, record_telemetry

from backend.novelty.scoring.base import compute_base_score
from backend.novelty.scoring.bonuses import compute_bonuses
from backend.novelty.scoring.blending import blend
from backend.novelty.scoring.penalties import compute_saturation_penalty, compute_admin_penalty

from backend.core.db import db
from backend.core.models import ProjectIdea, Domain


from backend.novelty.utils.signals import compute_similarity_stats, compute_specificity_signal, compute_temporal_signal
from backend.novelty.normalization import determine_level, normalize_score
from backend.novelty.explain import generate_explanation, generate_detailed_explanation
from backend.novelty.utils.calibration import compute_evidence_score, apply_evidence_constraints

from backend.retrieval.orchestrator import retrieve_sources
from backend.semantic.embedder import Embedder

logger = logging.getLogger(__name__)


class NoveltyAnalyzer:
    def __init__(self):
        self.embedder = Embedder()

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

    def _check_commodity_pattern(self, description: str) -> float:
        """Check if the idea matches common commodity/generic patterns.
        Returns a penalty multiplier (0.0 = no penalty, up to -15)."""
        desc_lower = description.lower()
        matches = sum(1 for p in COMMODITY_PATTERNS if p in desc_lower)
        if matches >= 3:
            return -15.0
        elif matches >= 2:
            return -10.0
        elif matches >= 1:
            return -5.0
        return 0.0

    def _compute_internal_reuse_penalty(self, sources: list) -> float:
        """Penalty based on how many existing ideas share the same source URLs.
        High reuse = the idea is retreading covered ground."""
        if not sources:
            return 0.0
        from backend.core.models import IdeaSource
        source_urls = [s.get("url") for s in sources if s.get("url")]
        if not source_urls:
            return 0.0
        # Count how many distinct ideas reference these same URLs
        try:
            reuse_count = db.session.query(
                db.func.count(db.func.distinct(IdeaSource.idea_id))
            ).filter(IdeaSource.url.in_(source_urls)).scalar() or 0
        except Exception:
            return 0.0
        # Scale: 0 reuse = 0 penalty, 5+ = -10
        if reuse_count >= 5:
            return -10.0
        elif reuse_count >= 3:
            return -5.0
        elif reuse_count >= 1:
            return -2.0
        return 0.0

    def analyze(self, description: str, domain: str, problem_class: str = "general"):
        sources = retrieve_sources(
            query=description,
            domain=domain,
            problem_class=problem_class,
            limit=50,
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
        # Also track relevance tiers for evidence calibration
        sanitized_sources = []
        tier_breakdown = {"supporting": 0, "contextual": 0, "peripheral": 0}
        
        for s in sources[:20]:
            relevance_tier = s.get("relevance_tier", "contextual")
            tier_breakdown[relevance_tier] = tier_breakdown.get(relevance_tier, 0) + 1
            
            # Generate relevance explanation based on source type and tier
            relevance_explanation = ""
            if s.get("source_type") == "arxiv":
                if s.get("metadata", {}).get("query_variation_quality") == "domain_only":
                    relevance_explanation = f"Matched domain keywords; problem-type relevance is weaker."
                else:
                    src_problem_class = s.get("problem_class", "general")
                    relevance_explanation = f"Relevant to {src_problem_class} class."
            else:  # github
                relevance_explanation = "Practical implementation example."
            
            sanitized_sources.append({
                "title": s.get("title") or s.get("name") or (s.get("url") or ""),
                "url": s.get("url"),
                "source_type": s.get("source_type"),
                "summary": _truncate(s.get("summary") or s.get("snippet") or s.get("description") or ""),
                "confidence": s.get("confidence"),
                "relevance_tier": relevance_tier,
                "relevance_explanation": relevance_explanation,
                "problem_type_match": s.get("relevance_class", "indirect"),
                "similarity_score": s.get("similarity_score_adjusted") or s.get("similarity_score", 0),
            })


        # Compute bonuses based on the final sanitized source count
        bonus = compute_bonuses(description, domain, source_count=len(sanitized_sources))

        # HITL penalty from shared-source ideas
        hitl_penalty = self._compute_hitl_penalty(sources)

        # Admin penalty from domain-level verdict stats
        try:
            rejection_rate, validation_rate = self._admin_stats(domain)
            admin_penalty = compute_admin_penalty(rejection_rate, validation_rate)
        except Exception:
            admin_penalty = 0.0
            rejection_rate, validation_rate = 0.0, 0.0

        # Commodity pattern penalty
        commodity_penalty = self._check_commodity_pattern(description)

        # Internal reuse penalty (how many existing ideas share these sources)
        reuse_penalty = self._compute_internal_reuse_penalty(sources)

        # Domain maturity adjustment
        maturity = DOMAIN_MATURITY.get(domain, "mature")
        if maturity == "emerging":
            maturity_bonus = 5.0  # Emerging domains get novelty boost
        elif maturity == "growing":
            maturity_bonus = 2.0
        else:
            maturity_bonus = 0.0

        total_adjustments = bonus + hitl_penalty + admin_penalty + commodity_penalty + reuse_penalty + maturity_bonus
        score = blend(base * 0.9, base + total_adjustments)
        score = min(score, 100.0)  # Cap before domain weight to prevent overflow

        # Penalize if too many peripheral sources
        confidence_override = None
        peripheral_penalty_note = None
        if tier_breakdown["peripheral"] > tier_breakdown["supporting"] * 2:
            score = score * 0.85  # 15% penalty
            confidence_override = "Low"
            peripheral_penalty_note = "Novelty assessment has lower confidence: many retrieved sources are tangentially related rather than directly relevant to this problem type."

        weighted = score * DOMAIN_NOVELTY_WEIGHT.get(domain, DOMAIN_NOVELTY_WEIGHT.get(domain.lower(), 1.0))
        stabilized = check_stability(description + domain, weighted, "Medium")

        # Normalize score to engine caps before mapping to level
        normalized = normalize_score(stabilized, "software")

        # Determine confidence before calibration
        if len(sanitized_sources) >= 8:
            raw_confidence = "High"
        elif len(sanitized_sources) >= 3:
            raw_confidence = "Medium"
        else:
            raw_confidence = "Low"
        if confidence_override:
            raw_confidence = confidence_override

        # Apply evidence-based calibration constraints (was dead code, now active)
        evidence_score = compute_evidence_score(
            debug={"retrieved_sources": len(sources), "similarity_variance": sim_stats.get("variance", 0.5)},
            intent_confidence=0.8,  # default; overridden when routing metadata available
            sources=sanitized_sources,
        )

        calibrated = apply_evidence_constraints(
            result={
                "novelty_score": normalized,
                "novelty_level": determine_level(normalized),
                "confidence": raw_confidence,
            },
            evidence=evidence_score,
            sources=sanitized_sources,
        )

        final_score = calibrated["novelty_score"]
        final_level = calibrated["novelty_level"]
        final_confidence = calibrated["confidence"]

        # Generate basic explanations
        explanations = generate_explanation(
            novelty_score=final_score,
            similarity_stats=sim_stats,
            source_count=len(sanitized_sources),
            avg_popularity_penalty=saturation,
            sources=sources,
        )

        if peripheral_penalty_note:
            explanations.append(f"⚠️ {peripheral_penalty_note}")

        # Generate detailed explanation with signal breakdown (was dead code, now active)
        signal_breakdown = {
            "base_score": round(base, 1),
            "bonus": round(bonus, 1),
            "hitl_penalty": round(hitl_penalty, 1),
            "admin_penalty": round(admin_penalty, 1),
            "commodity_penalty": round(commodity_penalty, 1),
            "reuse_penalty": round(reuse_penalty, 1),
            "maturity_bonus": round(maturity_bonus, 1),
        }
        penalties = {
            "domain_weight": DOMAIN_NOVELTY_WEIGHT.get(domain, DOMAIN_NOVELTY_WEIGHT.get(domain.lower(), 1.0)),
            "peripheral_penalty": 0.85 if confidence_override else 1.0,
        }

        admin_validated_count = 0
        try:
            admin_validated_count = sum(
                1 for s in sanitized_sources
                if s.get("admin_validated_count", 0) > 0
            )
        except Exception:
            pass

        detailed_explanation = generate_detailed_explanation(
            novelty_score=final_score,
            confidence_tier=final_confidence,
            signal_breakdown=signal_breakdown,
            penalties=penalties,
            source_count=len(sanitized_sources),
            admin_validated_count=admin_validated_count,
        )

        record_telemetry("novelty.software.score", final_score)

        # Expanded trace payload for debugging
        trace_payload = {
            "score_raw": round(stabilized, 1),
            "score_normalized": normalized,
            "score_calibrated": final_score,
            "base": round(base, 2),
            "bonus": round(bonus, 2),
            "hitl_penalty": round(hitl_penalty, 2),
            "admin_penalty": round(admin_penalty, 2),
            "commodity_penalty": round(commodity_penalty, 2),
            "reuse_penalty": round(reuse_penalty, 2),
            "maturity_bonus": round(maturity_bonus, 2),
            "weighted": round(weighted, 2),
            "evidence_score": evidence_score,
            "signals": signals,
            "sources_count": len(sanitized_sources),
            "tier_breakdown": tier_breakdown,
            "domain_maturity": maturity,
            "admin_stats": {"rejection_rate": round(rejection_rate, 3), "validation_rate": round(validation_rate, 3)},
            "confidence_hint": final_confidence,
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
            "novelty_score": final_score,
            "novelty_level": final_level,
            "confidence": final_confidence,
            "evidence_score": round(evidence_score, 2),
            "explanations": explanations,
            "detailed_explanation": detailed_explanation,
            "insights": insights,
            "sources": sanitized_sources,
            "evidence_breakdown": tier_breakdown,
            "engine": "software",
            "trace_id": trace_id,
            "speculative": calibrated.get("speculative", False),
            "evidence_note": calibrated.get("evidence_note"),
            "signal_breakdown": signal_breakdown,
            "debug": {
                "retrieved_sources": len(sources),
                "sanitized_sources": len(sanitized_sources),
                "similarity_variance": sim_stats.get("variance", 0.5),
            },
        }
