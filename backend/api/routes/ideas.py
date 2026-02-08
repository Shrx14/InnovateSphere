"""
Idea-related endpoints (feedback, user ideas, detail views)
"""
import logging
from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from backend.core.db import db
from backend.core.models import (
    ProjectIdea, IdeaRequest, IdeaFeedback, IdeaView, AdminVerdict, Domain, GenerationTrace, ViewEvent
)
from backend.novelty.explain import generate_detailed_explanation

from backend.utils import get_current_user_id, serialize_full_idea

logger = logging.getLogger(__name__)


ideas_bp = Blueprint("ideas", __name__)


@ideas_bp.route("/api/ideas/<int:idea_id>/feedback", methods=["POST"])

@ideas_bp.route("/api/ideas/<int:idea_id>/novelty-explanation", methods=["GET"])
@jwt_required()
def get_novelty_explanation(idea_id):
    """
    Get detailed explanation of novelty score for an idea.
    Explains signals, confidence, and penalties applied.
    """
    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    # Users can only see explanations for their own ideas
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401
    
    is_owner = IdeaRequest.query.filter_by(
        user_id=user_id, idea_id=idea_id
    ).first() is not None
    
    if not is_owner:
        return jsonify({"error": "Access denied. You can only view explanations for your own ideas."}), 403

    # Get generation trace
    trace = GenerationTrace.query.filter_by(idea_id=idea_id).first()
    
    # Extract comprehensive signal breakdown
    signal_breakdown = {}
    penalties = {}
    comparable_sources = []
    
    if trace:
        # Extract signals from phase analysis
        if trace.phase_1_output and isinstance(trace.phase_1_output, dict):
            landscape = trace.phase_1_output
            # Map landscape analysis to signal contributions
            if landscape.get("gaps"):
                signal_breakdown["gaps_identified"] = 15.0
            if landscape.get("saturated_areas"):
                signal_breakdown["saturation_penalty"] = -10.0
            if landscape.get("emerging_trends"):
                signal_breakdown["emerging_trend_bonus"] = 10.0
        
        # Extract novelty context from phase 2 and 4
        if trace.phase_2_output and isinstance(trace.phase_2_output, dict):
            problem = trace.phase_2_output
            if problem.get("novelty_analysis"):
                novelty_analysis = problem.get("novelty_analysis", {})
                if novelty_analysis.get("distinctiveness") == "high":
                    signal_breakdown["high_distinctiveness"] = 12.0
        
        # Extract penalties from constraints
        if trace.bias_penalties_applied:
            penalties = trace.bias_penalties_applied.get("source_penalties", {})
            if penalty_urls := [url for url, mult in penalties.items() if mult < 1.0]:
                signal_breakdown["source_penalties"] = -float(len(penalty_urls) * 5)
        
        # Extract comparable sources from final output
        if trace.phase_4_output and isinstance(trace.phase_4_output, dict):
            if evidence_sources := trace.phase_4_output.get("evidence_sources", []):
                comparable_sources = [
                    {
                        "title": s.get("title", "Unknown"),
                        "url": s.get("url", ""),
                        "source_type": s.get("source_type", "unknown"),
                        "used_for": s.get("used_for", "")
                    }
                    for s in evidence_sources[:3]  # Top 3 comparable sources
                ]
    
    # Calculate contribution percentages
    total_signal = sum(abs(v) for v in signal_breakdown.values())
    signal_percentages = {
        k: round((v / total_signal * 100) if total_signal > 0 else 0, 1)
        for k, v in signal_breakdown.items()
    }
    
    # Generate detailed explanation
    explanation = generate_detailed_explanation(
        novelty_score=idea.novelty_score_cached or 65,
        confidence_tier=idea.novelty_confidence or "Medium",
        signal_breakdown=signal_breakdown or (idea.novelty_context.get("signals", {}) if idea.novelty_context else {}),
        penalties=penalties,
        source_count=len(idea.sources),
        admin_validated_count=sum(1 for s in idea.sources if s)
    )
    
    return jsonify({
        "idea_id": idea_id,
        "novelty_score": idea.novelty_score_cached or 65,
        "explanation": explanation,
        "signal_breakdown": {
            "signals": signal_breakdown,
            "percentages": signal_percentages,
            "total_signals": total_signal
        },
        "penalties_applied": {
            "source_penalties": penalties,
            "domain_strictness": trace.constraints_active.get("domain_strictness", 1.0) if trace and trace.constraints_active else 1.0
        },
        "comparable_sources": comparable_sources,
        "sources_analyzed": len(idea.sources),
        "evidence_strength": idea.evidence_strength,
        "hallucination_risk": idea.hallucination_risk_level,
        "trace_available": trace is not None
    }), 200

@jwt_required()
def submit_idea_feedback(idea_id):
    """
    Submit structured feedback on idea quality.
    """
    data = request.get_json() or {}
    feedback_type = data.get("feedback_type")
    comment = data.get("comment", "").strip()

    if feedback_type not in ["factual_error", "hallucinated_source", "weak_novelty", "poor_justification", "unclear_scope", "high_quality"]:
        return jsonify({"error": "Invalid feedback_type"}), 400

    if len(comment) > 5000:
        return jsonify({"error": "Comment too long (maximum 5000 characters)"}), 400

    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    existing = IdeaFeedback.query.filter_by(
        user_id=user_id, idea_id=idea_id, feedback_type=feedback_type
    ).first()
    if existing:
        return jsonify({"error": "Feedback already submitted for this type"}), 409

    feedback = IdeaFeedback(
        user_id=user_id,
        idea_id=idea_id,
        feedback_type=feedback_type,
        comment=comment if comment else None
    )
    db.session.add(feedback)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Feedback already submitted for this type"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to submit feedback. Please try again."}), 500

    return jsonify({"message": "Feedback submitted successfully"}), 201


@ideas_bp.route("/api/ideas/mine", methods=["GET"])
@jwt_required()
def my_ideas():
    user_id = get_current_user_id()

    try:
        page = max(int(request.args.get("page", 1)), 1)
        limit = min(int(request.args.get("limit", 20)), 100)
    except ValueError:
        return jsonify({"error": "page and limit must be valid integers"}), 400

    query = (
        db.session.query(ProjectIdea)
        .join(IdeaRequest, IdeaRequest.idea_id == ProjectIdea.id)
        .join(Domain, Domain.id == ProjectIdea.domain_id)
        .outerjoin(AdminVerdict)
        .filter(IdeaRequest.user_id == user_id)
        .order_by(ProjectIdea.created_at.desc())
    )

    total = query.count()
    ideas = query.offset((page - 1) * limit).limit(limit).all()

    return jsonify({
        "ideas": [
            {
                "id": idea.id,
                "title": idea.title,
                "domain": idea.domain.name if idea.domain else None,
                "novelty_score": idea.novelty_score_cached,
                "quality_score": idea.quality_score_cached,
                "status": (
                    idea.admin_verdict.verdict
                    if idea.admin_verdict
                    else "pending"
                ),
                "created_at": idea.created_at.isoformat()
            }
            for idea in ideas
        ],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }), 200


@ideas_bp.route("/api/ideas/<int:idea_id>", methods=["GET"])
@jwt_required()
def authenticated_idea_detail(idea_id):
    """
    Authenticated endpoint to view individual idea details with trust signals.
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    if not idea.is_public and not any(req.user_id == user_id for req in idea.requests):
        return jsonify({"error": "Access denied"}), 403

    already_viewed = IdeaView.query.filter(
        IdeaView.idea_id == idea.id,
        IdeaView.user_id == user_id
    ).first()

    if not already_viewed:
        idea.view_count += 1
        db.session.add(
            IdeaView(idea_id=idea.id, user_id=user_id)
        )
        
        # Log view event for analytics
        try:
            view_event = ViewEvent(
                idea_id=idea.id,
                user_id=user_id,
                event_type="view",
                referrer="authenticated_detail"
            )
            db.session.add(view_event)
        except Exception as e:
            logger.warning(f"Failed to log ViewEvent: {e}")
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            # Duplicate view is okay, silently ignore
        except Exception as e:
            db.session.rollback()
            # Don't block idea viewing if view tracking fails
            pass

    return jsonify({
        "idea": serialize_full_idea(idea)
    }), 200
