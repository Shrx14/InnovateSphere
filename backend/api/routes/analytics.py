"""
Analytics endpoints (admin and user)
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from backend.core.db import db
from backend.core.app import cache
from backend.core.models import ProjectIdea, Domain, IdeaRequest, IdeaReview, AdminVerdict
from backend.utils import require_admin

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/api/analytics/admin/kpis", methods=["GET"])
@jwt_required()
def admin_kpis():
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    total_ideas = ProjectIdea.query.count()

    avg_novelty = (
        db.session.query(func.avg(ProjectIdea.novelty_score_cached))
        .filter(ProjectIdea.novelty_score_cached.isnot(None))
        .scalar()
    )
    avg_novelty = round(float(avg_novelty), 2) if avg_novelty else 0

    avg_quality = (
        db.session.query(func.avg(ProjectIdea.quality_score_cached))
        .filter(ProjectIdea.quality_score_cached.isnot(None))
        .scalar()
    )
    avg_quality = round(float(avg_quality), 2) if avg_quality else 0

    total_verdicts = AdminVerdict.query.count()
    rejected_count = AdminVerdict.query.filter(AdminVerdict.verdict == "rejected").count()
    rejection_rate = round((rejected_count / total_verdicts * 100), 1) if total_verdicts > 0 else 0

    return jsonify({
        "total_ideas": total_ideas,
        "avg_novelty": avg_novelty,
        "avg_quality": avg_quality,
        "rejection_rate": rejection_rate
    }), 200


@analytics_bp.route("/api/analytics/admin/domains", methods=["GET"])
@jwt_required()
def admin_domains():
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    rows = (
        db.session.query(
            Domain.name,
            func.count(ProjectIdea.id),
            func.count(IdeaRequest.id),
            func.avg(IdeaReview.rating),
        )
        .outerjoin(ProjectIdea)
        .outerjoin(IdeaRequest)
        .outerjoin(IdeaReview)
        .group_by(Domain.id)
        .all()
    )

    return jsonify(
        {
            "domains": [
                {
                    "domain": r[0],
                    "idea_count": r[1],
                    "request_count": r[2],
                    "average_rating": round(float(r[3]), 1) if r[3] else None,
                }
                for r in rows
            ]
        }
    ), 200


@analytics_bp.route("/api/analytics/admin/trends", methods=["GET"])
@jwt_required()
def admin_trends():
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    rows = (
        db.session.query(
            func.date(ProjectIdea.created_at).label("date"),
            func.count(ProjectIdea.id)
        )
        .group_by(func.date(ProjectIdea.created_at))
        .order_by(func.date(ProjectIdea.created_at))
        .all()
    )

    return jsonify({
        "trends": [
            {"date": str(r[0]), "count": r[1]}
            for r in rows
        ]
    }), 200


@analytics_bp.route("/api/analytics/admin/distributions", methods=["GET"])
@jwt_required()
def admin_distributions():
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    ideas = ProjectIdea.query.all()

    return jsonify({
        "novelty": [i.novelty_score_cached for i in ideas if i.novelty_score_cached is not None],
        "quality": [i.quality_score_cached for i in ideas if i.quality_score_cached is not None]
    }), 200


@analytics_bp.route("/api/analytics/admin/user-domains", methods=["GET"])
@jwt_required()
def admin_user_domains():
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    rows = (
        db.session.query(
            Domain.name,
            func.count(IdeaRequest.id)
        )
        .join(ProjectIdea, ProjectIdea.domain_id == Domain.id)
        .join(IdeaRequest, IdeaRequest.idea_id == ProjectIdea.id)
        .group_by(Domain.name)
        .all()
    )

    return jsonify({
        "domains": [
            {"domain": r[0], "requests": r[1]}
            for r in rows
        ]
    }), 200
