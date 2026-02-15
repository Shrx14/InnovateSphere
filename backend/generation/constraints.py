from typing import Dict, List, Any, Optional
from backend.core.db import db
from backend.core.models import ProjectIdea, AdminVerdict, IdeaFeedback, Domain

from backend.retrieval.source_reputation import get_source_reputation
from datetime import datetime, timedelta


def build_hitl_constraints(domain: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build HITL constraints from historical data.
    Constraints are deterministic and based on aggregate signals.
    """
    # Get domain ID
    domain_obj = Domain.query.filter_by(name=domain).first()
    if not domain_obj:
        return {
            "source_penalties": {},
            "pattern_penalties": [],
            "domain_strictness": 1.0
        }

    domain_id = domain_obj.id

    # Compute domain-level rejection/downgrade rates (last 30 days)
    cutoff = datetime.utcnow() - timedelta(days=30)
    recent_ideas = ProjectIdea.query.filter(
        ProjectIdea.domain_id == domain_id,
        ProjectIdea.created_at >= cutoff,
    ).all()

    total_ideas = len(recent_ideas)
    if total_ideas == 0:
        rejection_rate = 0.0
        downgrade_rate = 0.0
    else:
        rejected_count = sum(1 for idea in recent_ideas if idea.admin_verdict and idea.admin_verdict.verdict == "rejected")
        downgraded_count = sum(1 for idea in recent_ideas if idea.admin_verdict and idea.admin_verdict.verdict == "downgraded")
        rejection_rate = rejected_count / total_ideas
        downgrade_rate = downgraded_count / total_ideas

    # Domain strictness: 1.0 to 1.5
    domain_strictness = 1.0 + (rejection_rate * 0.3) + (downgrade_rate * 0.2)
    domain_strictness = min(1.5, max(1.0, domain_strictness))

    # Source penalties from reputation
    reputation = get_source_reputation()
    source_penalties = {}
    for src in sources:
        url = src.get("url")
        if url in reputation:
            rep = reputation[url]
            total_verdicts = rep["rejected"] + rep["downgraded"] + rep["validated"]
            if total_verdicts > 0:
                rejected_ratio = rep["rejected"] / total_verdicts
                downgraded_ratio = rep["downgraded"] / total_verdicts
                validated_ratio = rep["validated"] / total_verdicts

                # Multipliers: rejected strong negative, downgraded mild negative, validated small positive
                multiplier = 1.0
                multiplier -= rejected_ratio * 0.5  # up to -0.5 for all rejected
                multiplier -= downgraded_ratio * 0.2  # up to -0.2 for all downgraded
                multiplier += validated_ratio * 0.1  # up to +0.1 for all validated
                source_penalties[url] = max(0.1, multiplier)  # floor at 0.1 to avoid zero

    # Pattern penalties: simple list of rejected idea titles for structural matching
    rejected_ideas = ProjectIdea.query.filter(
        ProjectIdea.admin_verdict.has(verdict="rejected"),
        ProjectIdea.domain_id == domain_id,
    ).all()
    pattern_penalties = [idea.title.lower() for idea in rejected_ideas]

    return {
        "source_penalties": source_penalties,
        "pattern_penalties": pattern_penalties,
        "domain_strictness": domain_strictness
    }


def is_rejected_pattern(candidate_idea: Dict[str, Any], constraints: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Check if candidate idea matches historically rejected patterns.
    Uses both title matching and embedding similarity (when available).
    """
    candidate_title = candidate_idea.get("title", "").lower()
    candidate_problem = candidate_idea.get("problem_formulation", {}).get("context", "").lower()

    # 1) Exact title match
    for rejected_title in constraints.get("pattern_penalties", []):
        if candidate_title == rejected_title:
            return {
                "error": "generation_aborted",
                "reason": "historically_rejected_pattern",
                "message": "Similar ideas using these sources were previously rejected by reviewers.",
                "confidence": "low"
            }

    # 2) Embedding-based similarity check (if embedder is available)
    try:
        from backend.semantic.embedder import get_embedder
        embedder = get_embedder()
        if embedder and candidate_title and constraints.get("pattern_penalties"):
            candidate_emb = embedder.encode(candidate_title)
            for rejected_title in constraints["pattern_penalties"]:
                rejected_emb = embedder.encode(rejected_title)
                similarity = _cosine_similarity(candidate_emb, rejected_emb)
                if similarity > 0.85:  # High similarity threshold
                    return {
                        "error": "generation_aborted",
                        "reason": "embedding_similar_to_rejected",
                        "message": f"This idea is structurally similar to a previously rejected idea (similarity: {similarity:.2f}).",
                        "confidence": "medium",
                        "similar_to": rejected_title
                    }
    except Exception:
        pass  # Embedder not available or failed, skip embedding check

    return None


def filter_hallucinated_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out sources that have been flagged as hallucinated in the database.
    """
    from backend.core.models import IdeaSource
    flagged_urls = set()
    try:
        flagged = IdeaSource.query.filter_by(is_hallucinated=True).with_entities(IdeaSource.url).all()
        flagged_urls = {row.url for row in flagged}
    except Exception:
        pass  # If DB query fails, don't block generation

    if not flagged_urls:
        return sources

    filtered = [s for s in sources if s.get("url") not in flagged_urls]
    return filtered


def _cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    import math
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
