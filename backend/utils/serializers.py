"""
Serialization utilities for idea models.
"""
from backend.core.models import AdminVerdict


def serialize_public_idea(idea):
    """
    Serialize an idea for public/anonymous viewing.
    Excludes trust signals and sensitive data.
    """
    return {
        "id": idea.id,
        "title": idea.title,
        "problem_statement": idea.problem_statement,
        "tech_stack": idea.tech_stack,
        "tech_stack_json": idea.tech_stack_json,
        "domain": idea.domain.name if idea.domain else None,
        "novelty_score": idea.novelty_score_cached,
        "quality_score": idea.quality_score_cached,
        "view_count": idea.view_count,
    }


def serialize_full_idea(idea):
    """
    Serialize an idea with full details including trust signals.
    For authenticated users only.
    """
    data = serialize_public_idea(idea)
    data.update(
        {
            "ai_pipeline_version": idea.ai_pipeline_version,
            "is_ai_generated": idea.is_ai_generated,
            "is_public": idea.is_public,
            "created_at": idea.created_at.isoformat(),
            "view_count": idea.view_count,
            "sources": [
                {
                    "id": s.id,
                    "source_type": s.source_type,
                    "title": s.title,
                    "url": s.url,
                    "published_date": s.published_date.isoformat()
                    if s.published_date
                    else None,
                    "summary": s.summary,
                    "is_hallucinated": s.is_hallucinated,
                    "relevance_tier": s.relevance_tier or "supporting",
                }
                for s in idea.sources
            ],
            "reviews": [
                {
                    "rating": r.rating,
                    "comment": r.comment,
                    "created_at": r.created_at.isoformat(),
                }
                for r in idea.reviews
            ],
            "average_rating": round(
                sum(r.rating for r in idea.reviews) / len(idea.reviews), 1
            )
            if idea.reviews
            else None,
            "requested_count": len(idea.requests),
            # Segment 3.2: Trust signals for authenticated users only
            "quality_score": idea.quality_score_cached,
            "novelty_score": idea.novelty_score_cached,
            "status": idea.admin_verdict.verdict if idea.admin_verdict else "pending",
            "novelty_confidence": idea.novelty_confidence,
            "evidence_strength": idea.evidence_strength,
            "hallucination_risk_level": idea.hallucination_risk_level,
            "novelty_explanation": idea.novelty_context.get('explanation', 'Novelty evaluated based on multi-source analysis across research papers, code repositories, and prior work.') if idea.novelty_context else 'Novelty evaluated based on multi-source analysis across research papers, code repositories, and prior work.',
            "admin_verdict": idea.admin_verdict.verdict if idea.admin_verdict else None,
            "warning": "This idea is experimental and under review." if idea.admin_verdict and idea.admin_verdict.verdict == "rejected" else None,
            "evaluation_metrics": (
                idea.novelty_context.get("evaluation", {})
                if isinstance(idea.novelty_context, dict)
                else {}
            ),
        }
    )
    return data
