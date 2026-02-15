"""
Admin endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from backend.core.db import db
from backend.core.models import (
    ProjectIdea, IdeaFeedback, IdeaSource, AdminVerdict, Domain, GenerationTrace
)
from backend.novelty.explain import generate_detailed_explanation
from backend.utils import require_admin, get_current_user_id, serialize_public_idea, serialize_full_idea
from backend.ai.registry import get_active_bias_profile

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/api/admin/ideas/<int:idea_id>/bias-breakdown", methods=["GET"])
@jwt_required()
def admin_get_bias_breakdown(idea_id):
    """
    Get detailed bias and penalty breakdown for an idea.
    Shows admins how bias penalties affected the final novelty score.
    """
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    trace = GenerationTrace.query.filter_by(idea_id=idea_id).first()
    if not trace:
        return jsonify({"error": "Generation trace not found for this idea"}), 404

    # Extract penalties and constraints from trace
    constraints = trace.constraints_active or {}
    penalties = trace.bias_penalties_applied or {}
    
    # Get source penalties for transparency
    source_penalties = constraints.get("source_penalties", {})
    domain_strictness = constraints.get("domain_strictness", 1.0)
    
    penalized_sources = [
        {
            "url": url,
            "penalty_multiplier": mult,
            "reason": "Source marked as rejected" if mult < 0.5 else "Source downgraded"
        }
        for url, mult in source_penalties.items()
        if mult < 1.0
    ]
    
    # Generate detailed explanation
    detailed_explanation = generate_detailed_explanation(
        novelty_score=idea.novelty_score_cached or 0,
        confidence_tier=idea.novelty_confidence or "Medium",

        signal_breakdown=idea.novelty_context.get("signal_weights", {}) if idea.novelty_context else {},
        penalties=penalties.get("source_penalties", {}),
        source_count=len(idea.sources),
        admin_validated_count=sum(1 for v in source_penalties.values() if v >= 1.0)
    )
    
    return jsonify({
        "idea_id": idea_id,
        "title": idea.title,
        "novelty_score": idea.novelty_score_cached or 0,

        "domain_strictness": domain_strictness,
        "penalized_sources": penalized_sources,
        "detailed_explanation": detailed_explanation,
        "constraints": {
            "domain_strictness": domain_strictness,
            "active_penalties": list(penalties.keys()),
            "penalized_source_count": len(penalized_sources)
        }
    }), 200


@admin_bp.route("/api/admin/ideas/<int:idea_id>/generation-trace", methods=["GET"])
@jwt_required()
def admin_get_generation_trace(idea_id):
    """
    Get the complete generation trace for an idea.
    Shows Phase 0-4 reasoning: landscape analysis, problem framing, evidence validation, synthesis.
    For admins only - provides transparency into how an idea was generated.
    """
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    trace = GenerationTrace.query.filter_by(idea_id=idea_id).first()
    if not trace:
        return jsonify({"error": "Generation trace not found for this idea"}), 404

    return jsonify({
        "idea_id": idea_id,
        "title": idea.title,
        "domain": idea.domain.name if idea.domain else None,
        "generation_trace": {
            "query": trace.query,
            "domain_name": trace.domain_name,
            "ai_pipeline_version": trace.ai_pipeline_version,
            "bias_profile_version": trace.bias_profile_version,
            "bias_profile_rules": get_active_bias_profile().get("rules") if trace.bias_profile_version else None,
            "phase_0": {
                "name": "Input Conditioning",
                "description": "User query and domain selection",
                "output": trace.phase_0_output
            },
            "phase_1": {
                "name": "Live Retrieval",
                "description": "Retrieved sources from arXiv and GitHub",
                "output": trace.phase_1_output
            },
            "phase_2": {
                "name": "Idea Space Analysis",
                "description": "Landscape analysis: dominant patterns, gaps, saturated combinations",
                "output": trace.phase_2_output
            },
            "phase_3": {
                "name": "Problem Framing",
                "description": "Define problem informed by landscape analysis",
                "output": trace.phase_3_output
            },
            "phase_4": {
                "name": "Evidence Validation",
                "description": "Validate sources support the problem",
                "output": trace.phase_4_output
            },
            "phase_5": {
                "name": "Output Synthesis",
                "description": "Generate grounded, evidence-anchored idea",
                "output": trace.phase_4_output
            },
            "constraints_active": trace.constraints_active,
            "bias_penalties_applied": trace.bias_penalties_applied,
            "created_at": trace.created_at.isoformat() if trace.created_at else None
        }
    }), 200

@admin_bp.route("/api/admin/ideas/quality-review", methods=["GET"])
@jwt_required()
def admin_quality_review():
    """
    Admin review queue for ideas needing governance.
    """
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    try:
        page = max(int(request.args.get("page", 1)), 1)
        limit = min(int(request.args.get("limit", 20)), 100)
    except ValueError:
        return jsonify({"error": "page and limit must be valid integers"}), 400

    query = ProjectIdea.query.filter(
        db.or_(
            ProjectIdea.id.in_(
                db.session.query(IdeaFeedback.idea_id).filter(
                    db.or_(
                        IdeaFeedback.feedback_type == "hallucinated_source",
                        IdeaFeedback.feedback_type == "weak_novelty"
                    )
                ).group_by(IdeaFeedback.idea_id).having(func.count() >= 1)
            ),
            ProjectIdea.id.in_(
                db.session.query(IdeaSource.idea_id).group_by(IdeaSource.idea_id).having(func.count() < 3)
            )
        )
    ).order_by(ProjectIdea.created_at.desc())

    total = query.count()
    ideas = query.offset((page - 1) * limit).limit(limit).all()

    result = []
    for idea in ideas:
        feedback_breakdown = {}
        for fb in idea.feedbacks:
            feedback_breakdown[fb.feedback_type] = feedback_breakdown.get(fb.feedback_type, 0) + 1

        result.append({
            "id": idea.id,
            "title": idea.title,
            "domain": idea.domain.name if idea.domain else None,
            "novelty_score": idea.novelty_score_cached or 0,
            "quality_score": idea.quality_score,
            "hallucination_risk_level": idea.hallucination_risk_level,
            "evidence_strength": idea.evidence_strength,
            "feedback_summary": feedback_breakdown,
            "source_count": len(idea.sources),
        })

    return jsonify({
        "ideas": result,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }), 200


@admin_bp.route("/api/admin/ideas/<int:idea_id>", methods=["GET"])
@jwt_required()
def admin_idea_detail(idea_id):
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    feedback_history = [
        {
            "id": fb.id,
            "feedback_type": fb.feedback_type,
            "comment": fb.comment,
            "created_at": fb.created_at.isoformat(),
            "user_id": fb.user_id,
        }
        for fb in idea.feedbacks
    ]

    return jsonify({
        "id": idea.id,
        "title": idea.title,
        "problem_statement": idea.problem_statement,
        "tech_stack": idea.tech_stack,
        "domain": idea.domain.name if idea.domain else None,
        "ai_pipeline_version": idea.ai_pipeline_version,
        "is_ai_generated": idea.is_ai_generated,
        "is_public": idea.is_public,
        "created_at": idea.created_at.isoformat(),
        "sources": [
            {
                "id": s.id,
                "source_type": s.source_type,
                "title": s.title,
                "url": s.url,
                "published_date": s.published_date.isoformat() if s.published_date else None,
                "summary": s.summary,
                "is_hallucinated": s.is_hallucinated,
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
        "average_rating": round(sum(r.rating for r in idea.reviews) / len(idea.reviews), 1) if idea.reviews else None,
        "requested_count": len(idea.requests),
        "quality_score": idea.quality_score,
        "novelty_confidence": idea.novelty_confidence,
        "evidence_strength": idea.evidence_strength,
        "hallucination_risk_level": idea.hallucination_risk_level,
        "admin_verdict": idea.admin_verdict.verdict if idea.admin_verdict else None,
        "is_human_verified": idea.is_human_verified,
        "feedback_history": feedback_history,
    }), 200


@admin_bp.route("/api/admin/ideas/<int:idea_id>/verdict", methods=["POST"])
@jwt_required()
def admin_verdict(idea_id):
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}
    verdict = data.get("verdict")
    reason = data.get("reason", "").strip()

    if verdict not in ("validated", "downgraded", "rejected"):
        return jsonify({"error": "Invalid verdict"}), 400

    if verdict == "rejected" and not reason:
        return jsonify({"error": "Reason required for rejection"}), 400

    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    if idea.admin_verdict:
        # Allow verdict update instead of blocking with 409
        existing = idea.admin_verdict
        existing.verdict = verdict
        existing.reason = reason
        existing.admin_id = get_current_user_id()
    else:
        db.session.add(AdminVerdict(
            idea_id=idea_id,
            admin_id=get_current_user_id(),
            verdict=verdict,
            reason=reason,
        ))

    # Sync validated flag
    idea.is_validated = (verdict == "validated")

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Verdict conflict"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save verdict. Please try again."}), 500

    return jsonify({"message": f"Idea {verdict}"}), 201


@admin_bp.route("/api/admin/abuse-events", methods=["GET"])
@jwt_required()
def admin_list_abuse_events():
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    try:
        page = max(int(request.args.get("page", 1)), 1)
        limit = min(int(request.args.get("limit", 50)), 200)
    except ValueError:
        return jsonify({"error": "page and limit must be valid integers"}), 400

    from backend.core.models import AbuseEvent

    query = AbuseEvent.query.order_by(AbuseEvent.created_at.desc())
    total = query.count()
    rows = query.offset((page - 1) * limit).limit(limit).all()

    events = [
        {
            "id": e.id,
            "user_id": e.user_id,
            "event_type": e.event_type,
            "details": e.details,
            "created_at": e.created_at.isoformat(),
        }
        for e in rows
    ]

    return jsonify({"events": events, "meta": {"page": page, "limit": limit, "total": total}}), 200


@admin_bp.route("/api/admin/ideas/<int:idea_id>/rescore", methods=["POST"])
@jwt_required()
def admin_rescore_idea(idea_id):
    """
    Re-run novelty scoring for an idea and update cached scores.
    Useful after admin verdicts change the HITL constraint landscape.
    """
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    try:
        from backend.novelty.service import analyze_novelty
        result = analyze_novelty(
            idea.problem_statement or idea.title,
            idea.domain.name if idea.domain else "generic"
        )

        old_novelty = idea.novelty_score_cached
        idea.novelty_score_cached = result.get("novelty_score", old_novelty)
        idea.novelty_context = result
        idea.quality_score_cached = idea.quality_score

        db.session.commit()

        return jsonify({
            "message": "Idea rescored",
            "old_novelty": old_novelty,
            "new_novelty": idea.novelty_score_cached,
            "new_quality": idea.quality_score_cached
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Rescore failed: {str(e)}"}), 500


@admin_bp.route("/api/admin/ideas/<int:idea_id>/human-verified", methods=["POST"])
@jwt_required()
def admin_toggle_human_verified(idea_id):
    """
    Toggle the is_human_verified flag on an idea.
    Request: { "verified": true/false }
    """
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}
    verified = data.get("verified")
    if not isinstance(verified, bool):
        return jsonify({"error": "'verified' must be a boolean"}), 400

    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    idea.is_human_verified = verified

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update"}), 500

    return jsonify({
        "message": f"Idea {'verified' if verified else 'unverified'}",
        "is_human_verified": idea.is_human_verified
    }), 200


@admin_bp.route("/api/admin/ideas/<int:idea_id>/sources/<int:source_id>/hallucinated", methods=["POST"])
@jwt_required()
def admin_flag_hallucinated_source(idea_id, source_id):
    """
    Flag a source as hallucinated.
    Request: { "hallucinated": true/false }
    """
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    from backend.core.models import IdeaSource
    source = IdeaSource.query.filter_by(id=source_id, idea_id=idea_id).first()
    if not source:
        return jsonify({"error": "Source not found"}), 404

    data = request.get_json() or {}
    hallucinated = data.get("hallucinated", True)
    source.is_hallucinated = bool(hallucinated)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update"}), 500

    return jsonify({
        "message": f"Source {'flagged as hallucinated' if source.is_hallucinated else 'unflagged'}",
        "is_hallucinated": source.is_hallucinated
    }), 200
