import logging
import re
from collections import Counter

import numpy as np

from backend.core.config import Config
from backend.novelty.config import DOMAIN_NOVELTY_WEIGHT, DOMAIN_MATURITY, COMMODITY_PATTERNS
from backend.novelty.utils.observability import check_stability, trace_analysis, record_telemetry

from backend.novelty.scoring.base import compute_base_score
from backend.novelty.scoring.bonuses import compute_bonuses
from backend.novelty.scoring.blending import blend
from backend.novelty.scoring.penalties import compute_saturation_penalty, compute_admin_penalty

from backend.core.db import db
from backend.core.models import ProjectIdea, Domain


from backend.novelty.metrics import compute_similarity_distribution
from backend.novelty.utils.signals import compute_specificity_signal, compute_temporal_signal
from backend.novelty.normalization import determine_level, normalize_score
from backend.novelty.explain import generate_explanation, generate_detailed_explanation
from backend.novelty.utils.calibration import compute_evidence_score, apply_evidence_constraints

from backend.retrieval.orchestrator import retrieve_sources
from backend.retrieval.keyword_extractor import extract_key_terms_tfidf
from backend.semantic.embedder import get_embedder

logger = logging.getLogger(__name__)


class NoveltyAnalyzer:
    _APPROACH_HINTS = {
        "algorithm",
        "model",
        "architecture",
        "method",
        "pipeline",
        "optimization",
        "scheduling",
        "heuristic",
        "transformer",
        "lstm",
        "cnn",
        "graph",
        "federated",
        "bayesian",
        "reinforcement",
        "diffusion",
        "classification",
        "regression",
    }

    def __init__(self):
        self.embedder = get_embedder()

    @staticmethod
    def _tokenize_text(text: str) -> list[str]:
        if not text:
            return []
        return re.findall(r"[a-z0-9][a-z0-9_\-+/]{3,}", text.lower())

    def _compute_token_novelty(self, idea_text: str, source_texts: list[str]) -> tuple[float, list[str]]:
        source_tokens = []
        for text in source_texts:
            source_tokens.extend(self._tokenize_text(text))

        idea_vocab = set(self._tokenize_text(idea_text))
        if not idea_vocab:
            return 0.0, []

        freq = Counter(source_tokens)
        total_source_tokens = max(len(source_tokens), 1)

        novel_tokens = [
            token
            for token in sorted(idea_vocab)
            if (freq.get(token, 0) / total_source_tokens) < 0.001
        ]

        score = len(novel_tokens) / max(len(idea_vocab), 1)
        return min(max(score, 0.0), 1.0), novel_tokens[:10]

    def _extract_contrastive_terms(self, text: str, domain: str) -> dict:
        candidates = extract_key_terms_tfidf(text, max_terms=10)
        domain_tokens = [tok for tok in self._tokenize_text(domain.replace("&", " ")) if len(tok) > 2]

        approach_terms: list[str] = []
        domain_terms: list[str] = list(domain_tokens)

        for term in candidates:
            tokens = set(self._tokenize_text(term))
            if tokens & self._APPROACH_HINTS:
                approach_terms.append(term)
            else:
                domain_terms.append(term)

        if not approach_terms and candidates:
            approach_terms = candidates[: min(3, len(candidates))]

        if not domain_terms and candidates:
            domain_terms = candidates[min(1, len(candidates) - 1) : min(5, len(candidates))]

        # Deduplicate while preserving order.
        approach_terms = list(dict.fromkeys(approach_terms))
        domain_terms = list(dict.fromkeys(domain_terms))

        return {
            "approach_terms": approach_terms,
            "domain_terms": domain_terms,
            "approach_text": ", ".join(approach_terms),
            "domain_text": ", ".join(domain_terms),
        }

    def _compute_contrastive_signal(self, text: str, domain: str, source_embs: np.ndarray) -> dict:
        if not getattr(Config, "NOVELTY_ENABLE_CONTRASTIVE", True):
            return {
                "enabled": False,
                "signal": 0.0,
                "bonus": 0.0,
                "domain_similarity_mean": 0.0,
                "approach_similarity_mean": 0.0,
                "terms": {"approach_terms": [], "domain_terms": []},
            }

        terms = self._extract_contrastive_terms(text, domain)
        approach_text = terms.get("approach_text", "")
        domain_text = terms.get("domain_text", "")
        if not approach_text or not domain_text or source_embs.size == 0:
            return {
                "enabled": True,
                "signal": 0.0,
                "bonus": 0.0,
                "domain_similarity_mean": 0.0,
                "approach_similarity_mean": 0.0,
                "terms": terms,
            }

        approach_emb = self.embedder.encode([approach_text], normalize_embeddings=True)[0]
        domain_emb = self.embedder.encode([domain_text], normalize_embeddings=True)[0]

        approach_sims = np.asarray([float(np.dot(approach_emb, emb)) for emb in source_embs], dtype="float32")
        domain_sims = np.asarray([float(np.dot(domain_emb, emb)) for emb in source_embs], dtype="float32")

        domain_mean = float(np.mean(domain_sims)) if domain_sims.size else 0.0
        approach_mean = float(np.mean(approach_sims)) if approach_sims.size else 0.0

        min_domain_sim = float(getattr(Config, "NOVELTY_CONTRASTIVE_MIN_DOMAIN_SIM", 0.35))
        if domain_mean < min_domain_sim:
            signal = 0.0
        else:
            positive_delta = np.clip(domain_sims - approach_sims, 0.0, 1.0)
            top_delta = float(np.percentile(positive_delta, 75)) if positive_delta.size else 0.0
            mean_delta = float(np.mean(positive_delta)) if positive_delta.size else 0.0
            signal = min(max((top_delta * 0.6) + (mean_delta * 0.4), 0.0), 1.0)

        bonus = signal * float(getattr(Config, "NOVELTY_CONTRASTIVE_WEIGHT", 10.0))
        return {
            "enabled": True,
            "signal": signal,
            "bonus": bonus,
            "domain_similarity_mean": domain_mean,
            "approach_similarity_mean": approach_mean,
            "terms": terms,
        }

    def _compute_research_novelty(self, idea_text: str, query_text: str, source_texts: list[str], domain: str) -> dict:
        source_embs = self.embedder.encode(source_texts, normalize_embeddings=True)
        idea_emb = self.embedder.encode([idea_text], normalize_embeddings=True)[0]
        query_emb = self.embedder.encode([query_text], normalize_embeddings=True)[0]

        contrastive = self._compute_contrastive_signal(query_text or idea_text, domain, source_embs)

        query_sims = [float(np.dot(query_emb, emb)) for emb in source_embs]
        idea_sims = [float(np.dot(idea_emb, emb)) for emb in source_embs]

        if query_sims:
            query_max = float(np.max(query_sims))
            query_p90 = float(np.percentile(query_sims, 90))
            query_mean = float(np.mean(query_sims))
            query_novelty = 1.0 - (query_max * 0.4 + query_p90 * 0.3 + query_mean * 0.3)
        else:
            query_mean = 0.5
            query_novelty = 0.5

        if idea_sims:
            idea_max = float(np.max(idea_sims))
            idea_p75 = float(np.percentile(idea_sims, 75))
            idea_mean = float(np.mean(idea_sims))
            idea_novelty = 1.0 - (idea_max * 0.5 + idea_p75 * 0.3 + idea_mean * 0.2)
        else:
            idea_novelty = 0.5

        if len(query_sims) > 3:
            spread_signal = float(np.std(query_sims))
            cross_domain_bonus = spread_signal * 2.0 * (1.0 - query_mean)
        else:
            cross_domain_bonus = 0.0

        token_novelty, novel_tokens = self._compute_token_novelty(idea_text, source_texts)

        query_novelty = min(max(query_novelty, 0.0), 1.0)
        idea_novelty = min(max(idea_novelty, 0.0), 1.0)
        cross_domain_bonus = min(max(cross_domain_bonus, 0.0), 1.0)

        base_score = (
            idea_novelty * 40
            + query_novelty * 25
            + cross_domain_bonus * 20
            + token_novelty * 15
            + contrastive["bonus"]
        )

        return {
            "base_score": min(max(float(base_score), 0.0), 100.0),
            "query_novelty": query_novelty,
            "idea_novelty": idea_novelty,
            "cross_domain_bonus": cross_domain_bonus,
            "token_novelty": token_novelty,
            "query_sims": query_sims,
            "idea_sims": idea_sims,
            "novel_tokens": novel_tokens,
            "contrastive_signal": contrastive["signal"],
            "contrastive_bonus": contrastive["bonus"],
            "contrastive_terms": contrastive["terms"],
            "contrastive_domain_similarity_mean": contrastive["domain_similarity_mean"],
            "contrastive_approach_similarity_mean": contrastive["approach_similarity_mean"],
        }

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

    def analyze(
        self,
        description: str,
        domain: str,
        problem_class: str = "general",
        preloaded_sources: list | None = None,
        query_text: str | None = None,
    ):
        if preloaded_sources is not None:
            sources = preloaded_sources
        else:
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
                "novelty_score": 30.0,  # Low baseline when no references exist (was 50 — inflated)
                "novelty_level": determine_level(30.0),
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

        source_texts = [s.get("summary") or s.get("title") or "" for s in sources]
        novelty_components = self._compute_research_novelty(
            idea_text=description,
            query_text=(query_text or description),
            source_texts=source_texts,
            domain=domain,
        )

        sim_stats = compute_similarity_distribution(novelty_components["idea_sims"], domain=domain)
        specificity = compute_specificity_signal(description)
        temporal = compute_temporal_signal(sources)
        saturation = compute_saturation_penalty(len(sources))

        legacy_signals = {
            "similarity": sim_stats["mean_similarity"],
            "specificity": specificity,
            "temporal": temporal["recency_score"],
            "saturation": saturation,
        }

        legacy_base = compute_base_score(legacy_signals)
        base = novelty_components["base_score"] * 0.75 + legacy_base * 0.25

        # Helper to truncate long texts for summaries
        def _truncate(text: str, n: int = 400) -> str:
            if not text:
                return ""
            return text if len(text) <= n else text[: n - 1] + "…"

        # Sanitize sources for public API consumption (use for bonuses count)
        # Also track relevance tiers for evidence calibration
        sanitized_sources = []
        tier_breakdown = {"supporting": 0, "contextual": 0, "peripheral": 0}
        
        for idx, s in enumerate(sources[:20]):
            relevance_tier = s.get("relevance_tier", "contextual")
            tier_breakdown[relevance_tier] = tier_breakdown.get(relevance_tier, 0) + 1
            source_similarity = 0.0
            if idx < len(novelty_components["idea_sims"]):
                source_similarity = novelty_components["idea_sims"][idx]
            elif s.get("similarity_score_adjusted") is not None:
                source_similarity = s.get("similarity_score_adjusted")
            else:
                source_similarity = s.get("similarity_score", 0)
            
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
                "similarity_score": source_similarity,
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
        weighted = min(weighted, 100.0)  # Cap after domain weight to prevent overflow
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
            domain=domain,
        )

        if novelty_components.get("contrastive_bonus", 0.0) >= 0.5:
            explanations.append(
                "Contrastive method signal detected: idea approach appears differentiated from common methods within the same domain."
            )

        if peripheral_penalty_note:
            explanations.append(f"⚠️ {peripheral_penalty_note}")

        # Generate detailed explanation with signal breakdown (was dead code, now active)
        signal_breakdown = {
            "base_score": round(base, 1),
            "idea_novelty": round(novelty_components["idea_novelty"] * 100, 1),
            "domain_novelty": round(novelty_components["query_novelty"] * 100, 1),
            "cross_domain_bonus": round(novelty_components["cross_domain_bonus"] * 100, 1),
            "token_novelty": round(novelty_components["token_novelty"] * 100, 1),
            "contrastive_signal": round(novelty_components["contrastive_signal"] * 100, 1),
            "contrastive_bonus": round(novelty_components["contrastive_bonus"], 1),
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
            "signals": legacy_signals,
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
            "novel_tokens": novelty_components["novel_tokens"],
            "debug": {
                "retrieved_sources": len(sources),
                "sanitized_sources": len(sanitized_sources),
                "similarity_variance": sim_stats.get("variance", 0.5),
                "max_similarity": max(novelty_components["idea_sims"]) if novelty_components["idea_sims"] else 0.0,
                "p90_similarity": float(np.percentile(novelty_components["idea_sims"], 90)) if novelty_components["idea_sims"] else 0.0,
                "query_similarity_mean": float(np.mean(novelty_components["query_sims"])) if novelty_components["query_sims"] else 0.0,
                "contrastive_signal": novelty_components.get("contrastive_signal", 0.0),
                "contrastive_domain_similarity_mean": novelty_components.get("contrastive_domain_similarity_mean", 0.0),
                "contrastive_approach_similarity_mean": novelty_components.get("contrastive_approach_similarity_mean", 0.0),
                "contrastive_terms": novelty_components.get("contrastive_terms", {}),
            },
        }
