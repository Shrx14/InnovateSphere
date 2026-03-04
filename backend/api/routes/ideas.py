"""
Idea-related endpoints (feedback, user ideas, detail views)
"""
import logging
from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from backend.core.db import db
from backend.core.models import (
    ProjectIdea, IdeaRequest, IdeaFeedback, IdeaReview, IdeaView, AdminVerdict, Domain, GenerationTrace, ViewEvent
)
from backend.novelty.explain import generate_detailed_explanation

from backend.utils import get_current_user_id, serialize_full_idea

logger = logging.getLogger(__name__)


ideas_bp = Blueprint("ideas", __name__)


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
    trace = db.session.query(GenerationTrace).filter_by(idea_id=idea_id).first()
    
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
        novelty_score=idea.novelty_score_cached or 0,
        confidence_tier=idea.novelty_confidence or "Medium",

        signal_breakdown=signal_breakdown or (idea.novelty_context.get("signals", {}) if idea.novelty_context else {}),
        penalties=penalties,
        source_count=len(idea.sources),
        admin_validated_count=sum(1 for s in idea.sources if s)
    )
    
    return jsonify({
        "idea_id": idea_id,
        "novelty_score": idea.novelty_score_cached or 0,

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

@ideas_bp.route("/api/ideas/<int:idea_id>/feedback", methods=["POST"])
@jwt_required()
def submit_idea_feedback(idea_id):
    """
    Submit structured feedback on idea quality.
    """
    data = request.get_json() or {}
    feedback_type = data.get("feedback_type")
    comment = data.get("comment", "").strip()

    VALID_FEEDBACK_TYPES = [
        # Reaction types
        "upvote", "downvote", "bookmark", "report", "helpful", "not_helpful",
        # Quality-review types
        "factual_error", "hallucinated_source", "weak_novelty",
        "poor_justification", "unclear_scope", "high_quality"
    ]
    if feedback_type not in VALID_FEEDBACK_TYPES:
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
        # Refresh quality_score_cached after feedback (mirrors review endpoint behavior)
        idea.quality_score_cached = idea.quality_score
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Feedback already submitted for this type"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to submit feedback. Please try again."}), 500

    return jsonify({"message": "Feedback submitted successfully"}), 201


@ideas_bp.route("/api/ideas/<int:idea_id>/feedback", methods=["DELETE"])
@jwt_required()
def delete_idea_feedback(idea_id):
    """
    Remove feedback (e.g. unbookmark).
    Query param: ?feedback_type=bookmark
    """
    feedback_type = request.args.get("feedback_type")
    if not feedback_type:
        return jsonify({"error": "feedback_type query param required"}), 400

    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    existing = IdeaFeedback.query.filter_by(
        user_id=user_id, idea_id=idea_id, feedback_type=feedback_type
    ).first()
    if not existing:
        return jsonify({"error": "Feedback not found"}), 404

    db.session.delete(existing)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to remove feedback"}), 500

    return jsonify({"message": f"{feedback_type} removed"}), 200


@ideas_bp.route("/api/ideas/bookmarked", methods=["GET"])
@jwt_required()
def bookmarked_ideas():
    """
    List all ideas bookmarked by the current user.
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    try:
        page = max(int(request.args.get("page", 1)), 1)
        limit = min(int(request.args.get("limit", 20)), 100)
    except ValueError:
        return jsonify({"error": "page and limit must be valid integers"}), 400

    bookmark_idea_ids = (
        db.session.query(IdeaFeedback.idea_id)
        .filter(IdeaFeedback.user_id == user_id, IdeaFeedback.feedback_type == "bookmark")
    )

    query = (
        ProjectIdea.query
        .options(
            joinedload(ProjectIdea.domain),
            joinedload(ProjectIdea.admin_verdict),
        )
        .filter(ProjectIdea.id.in_(bookmark_idea_ids))
        .order_by(ProjectIdea.created_at.desc())
    )

    total = query.count()
    ideas = query.offset((page - 1) * limit).limit(limit).all()

    return jsonify({
        "ideas": [
            {
                "id": idea.id,
                "title": idea.title,
                "problem_statement": idea.problem_statement,
                "domain": idea.domain.name if idea.domain else None,
                "novelty_score": idea.novelty_score_cached,
                "quality_score": idea.quality_score_cached,
                "status": idea.admin_verdict.verdict if idea.admin_verdict else "pending",
                "created_at": idea.created_at.isoformat(),
            }
            for idea in ideas
        ],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        }
    }), 200


@ideas_bp.route("/api/ideas/<int:idea_id>/request", methods=["POST"])
@jwt_required()
def request_idea(idea_id):
    """
    Express demand for an idea. Prevents duplicates via user_id+idea_id.
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    existing = IdeaRequest.query.filter_by(user_id=user_id, idea_id=idea_id).first()
    if existing:
        return jsonify({"error": "Already requested", "requested_count": len(idea.requests)}), 409

    db.session.add(IdeaRequest(user_id=user_id, idea_id=idea_id))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Already requested"}), 409
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to submit request"}), 500

    return jsonify({
        "message": "Idea requested",
        "requested_count": len(idea.requests)
    }), 201


@ideas_bp.route("/api/ideas/mine", methods=["GET"])
@jwt_required()
def my_ideas():
    logger.debug("ENTER /api/ideas/mine: user_id=%s", get_current_user_id())
    user_id = get_current_user_id()

    try:
        page = max(int(request.args.get("page", 1)), 1)
        limit = min(int(request.args.get("limit", 20)), 100)
        logger.debug("Pagination params: page=%d, limit=%d", page, limit)
    except ValueError:
        logger.error("Invalid pagination params: page=%s, limit=%s", 
                    request.args.get("page"), request.args.get("limit"))
        return jsonify({"error": "page and limit must be valid integers"}), 400


    query = (
        db.session.query(ProjectIdea)
        .options(
            joinedload(ProjectIdea.domain),
            joinedload(ProjectIdea.admin_verdict),
        )
        .join(IdeaRequest, IdeaRequest.idea_id == ProjectIdea.id)
        .join(Domain, Domain.id == ProjectIdea.domain_id)
        .outerjoin(AdminVerdict)
        .filter(IdeaRequest.user_id == user_id)
        .order_by(ProjectIdea.created_at.desc())
    )

    total = query.count()
    ideas = query.offset((page - 1) * limit).limit(limit).all()
    
    logger.debug("Found %d total ideas, returning %d ideas for page %d", total, len(ideas), page)

    return jsonify({
        "ideas": [
            {
                "id": idea.id,
                "title": idea.title,
                "problem_statement": idea.problem_statement,
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

    idea = ProjectIdea.query.options(
        joinedload(ProjectIdea.domain),
        selectinload(ProjectIdea.sources),
        selectinload(ProjectIdea.feedbacks),
        selectinload(ProjectIdea.reviews),
        joinedload(ProjectIdea.admin_verdict),
        selectinload(ProjectIdea.requests),
    ).get(idea_id)
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


# ============================================================================
# Reviews (star-rating + optional comment)
# ============================================================================

@ideas_bp.route("/api/ideas/<int:idea_id>/review", methods=["POST"])
@jwt_required()
def submit_idea_review(idea_id):
    """
    Submit or update a star-rating review for an idea.
    Request: { "rating": 1-5, "comment": "optional" }
    One review per user per idea (upsert).
    """
    data = request.get_json() or {}
    rating = data.get("rating")
    comment = data.get("comment", "").strip()

    # Validate rating
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be an integer between 1 and 5"}), 400

    if len(comment) > 5000:
        return jsonify({"error": "Comment too long (maximum 5000 characters)"}), 400

    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    # Upsert: update existing review or create new
    existing = IdeaReview.query.filter_by(user_id=user_id, idea_id=idea_id).first()
    if existing:
        existing.rating = rating
        existing.comment = comment if comment else existing.comment
    else:
        review = IdeaReview(
            user_id=user_id,
            idea_id=idea_id,
            rating=rating,
            comment=comment if comment else None
        )
        db.session.add(review)

    # Update cached quality score
    try:
        db.session.flush()
        idea.quality_score_cached = idea.quality_score
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Review submission failed (duplicate)"}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Review submission error: {e}")
        return jsonify({"error": "Failed to submit review"}), 500

    return jsonify({
        "message": "Review submitted",
        "updated": existing is not None
    }), 201


@ideas_bp.route("/api/ideas/<int:idea_id>/reviews", methods=["GET"])
@jwt_required()
def list_idea_reviews(idea_id):
    """
    List all reviews for an idea.
    """
    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    reviews = IdeaReview.query.filter_by(idea_id=idea_id).order_by(
        IdeaReview.created_at.desc()
    ).all()

    return jsonify({
        "reviews": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at.isoformat()
            }
            for r in reviews
        ],
        "average_rating": round(
            sum(r.rating for r in reviews) / len(reviews), 1
        ) if reviews else None,
        "total_reviews": len(reviews)
    }), 200


@ideas_bp.route("/api/ideas/<int:idea_id>/feedbacks", methods=["GET"])
@jwt_required()
def list_idea_feedbacks(idea_id):
    """
    List all feedback entries for an idea (grouped by type).
    """
    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    feedbacks = IdeaFeedback.query.filter_by(idea_id=idea_id).order_by(
        IdeaFeedback.created_at.desc()
    ).all()

    # Group by type
    by_type = {}
    for fb in feedbacks:
        if fb.feedback_type not in by_type:
            by_type[fb.feedback_type] = []
        by_type[fb.feedback_type].append({
            "id": fb.id,
            "user_id": fb.user_id,
            "comment": fb.comment,
            "created_at": fb.created_at.isoformat()
        })

    return jsonify({
        "feedbacks": [
            {
                "id": fb.id,
                "feedback_type": fb.feedback_type,
                "comment": fb.comment,
                "user_id": fb.user_id,
                "created_at": fb.created_at.isoformat()
            }
            for fb in feedbacks
        ],
        "by_type": by_type,
        "total": len(feedbacks)
    }), 200
