"""
Idea-related endpoints (feedback, user ideas, detail views)
"""
from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from backend.core.db import db
from backend.core.models import (
    ProjectIdea, IdeaRequest, IdeaFeedback, IdeaView, AdminVerdict, Domain
)

from backend.utils import get_current_user_id, serialize_full_idea


ideas_bp = Blueprint("ideas", __name__)


@ideas_bp.route("/api/ideas/<int:idea_id>/feedback", methods=["POST"])
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
