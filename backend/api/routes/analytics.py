"""
Analytics endpoints (admin and user)
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from backend.core.db import db
from backend.core.app import cache, User
from backend.core.models import ProjectIdea, Domain, IdeaRequest, IdeaReview, IdeaFeedback, AdminVerdict, GenerationTrace
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

    # Rating distribution
    avg_rating = (
        db.session.query(func.avg(IdeaReview.rating))
        .scalar()
    )
    avg_rating = round(float(avg_rating), 2) if avg_rating else 0
    total_reviews = IdeaReview.query.count()

    # Feedback distribution
    feedback_counts = (
        db.session.query(IdeaFeedback.feedback_type, func.count(IdeaFeedback.id))
        .group_by(IdeaFeedback.feedback_type)
        .all()
    )
    feedback_distribution = {ftype: count for ftype, count in feedback_counts}
    total_feedbacks = sum(feedback_distribution.values())

    return jsonify({
        "total_ideas": total_ideas,
        "avg_novelty": avg_novelty,
        "avg_quality": avg_quality,
        "rejection_rate": rejection_rate,
        "avg_rating": avg_rating,
        "total_reviews": total_reviews,
        "total_feedbacks": total_feedbacks,
        "feedback_distribution": feedback_distribution
    }), 200




# ============================================================================
# Frontend-facing admin analytics endpoints (at /api/admin/... routes)
# ============================================================================

@analytics_bp.route("/api/admin/domains", methods=["GET"])
@jwt_required()
def admin_domains_frontend():
    """
    Admin endpoint: Domain statistics (counts, top ideas per domain)
    """
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    results = (
        db.session.query(
            Domain.name.label("name"),
            Domain.id.label("id"),
            func.count(ProjectIdea.id).label("idea_count"),
        )
        .outerjoin(ProjectIdea, Domain.id == ProjectIdea.domain_id)
        .group_by(Domain.id, Domain.name)
        .order_by(func.count(ProjectIdea.id).desc())
        .all()
    )

    return jsonify({
        "domains": [
            {
                "id": r.id,
                "name": r.name,
                "idea_count": r.idea_count or 0
            }
            for r in results
        ]
    }), 200


@analytics_bp.route("/api/admin/trends", methods=["GET"])
@jwt_required()
def admin_trends_frontend():
    """
    Admin endpoint: Time-series data (ideas created per day/week/month)
    """
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    from datetime import datetime, timedelta

    # Get last 30 days of data
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    results = (
        db.session.query(
            func.date(ProjectIdea.created_at).label("date"),
            func.count(ProjectIdea.id).label("count")
        )
        .filter(ProjectIdea.created_at >= thirty_days_ago)
        .group_by(func.date(ProjectIdea.created_at))
        .order_by(func.date(ProjectIdea.created_at))
        .all()
    )

    return jsonify({
        "trends": [
            {
                "date": str(r.date),
                "count": r.count
            }
            for r in results
        ]
    }), 200


@analytics_bp.route("/api/admin/distributions", methods=["GET"])
@jwt_required()
def admin_distributions_frontend():
    """
    Admin endpoint: Score distributions (novelty & quality histograms)
    """
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    ideas = ProjectIdea.query.all()

    novelty_scores = [idea.novelty_score_cached or 0 for idea in ideas]
    quality_scores = [idea.quality_score_cached or 0 for idea in ideas]

    # Create histograms (10-point buckets: 0-10, 10-20, etc.)
    def create_distribution(scores):
        buckets = {i: 0 for i in range(0, 101, 10)}
        for score in scores:
            bucket = min(int(score / 10) * 10, 100)
            buckets[bucket] += 1
        return [{"range": f"{k}-{k+10}", "count": v} for k, v in buckets.items()]

    return jsonify({
        "novelty": create_distribution(novelty_scores),
        "quality": create_distribution(quality_scores)
    }), 200


@analytics_bp.route("/api/admin/user-domains", methods=["GET"])
@jwt_required()
def admin_user_domains_frontend():
    """
    Admin endpoint: User domain preferences (how many users prefer each domain)
    """
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    results = (
        db.session.query(
            Domain.name.label("name"),
            Domain.id.label("id"),
            func.count(User.id).label("user_count")
        )
        .outerjoin(User, Domain.id == User.preferred_domain_id)
        .group_by(Domain.id, Domain.name)
        .order_by(func.count(User.id).desc())
        .all()
    )

    return jsonify({
        "user_domains": [
            {
                "id": r.id,
                "name": r.name,
                "user_count": r.user_count or 0
            }
            for r in results
        ]
    }), 200


@analytics_bp.route("/api/analytics/admin/bias-transparency", methods=["GET"])
@jwt_required()
def admin_bias_transparency():
    """
    Admin endpoint: Bias impact analysis
    Shows how HITL verdicts are affecting scores and generation patterns
    """
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403
    
    from backend.core.models import GenerationTrace
    
    # Get all generation traces with constraints
    traces = GenerationTrace.query.all()
    
    bias_impact_by_source = {}
    domain_strictness_distribution = {}
    penalty_impact_stats = {
        "total_ideas_with_penalties": 0,
        "average_penalty_impact": 0.0,
        "sources_affected": 0,
        "penalty_types": {}
    }
    
    total_penalty = 0.0
    ideas_with_penalties = 0
    
    for trace in traces:
        if not trace.constraints_active:
            continue
        
        # Track source penalties
        source_penalties = trace.constraints_active.get("source_penalties", {})
        if source_penalties:
            ideas_with_penalties += 1
            for url, multiplier in source_penalties.items():
                if multiplier < 1.0:
                    penalty_pct = int((1 - multiplier) * 100)
                    total_penalty += penalty_pct
                    
                    domain_key = url.split('/')[2] if '/' in url else 'unknown'
                    if domain_key not in bias_impact_by_source:
                        bias_impact_by_source[domain_key] = {
                            "count": 0,
                            "total_penalty": 0,
                            "avg_penalty": 0.0
                        }
                    bias_impact_by_source[domain_key]["count"] += 1
                    bias_impact_by_source[domain_key]["total_penalty"] += penalty_pct
                    bias_impact_by_source[domain_key]["avg_penalty"] = (
                        bias_impact_by_source[domain_key]["total_penalty"] / 
                        bias_impact_by_source[domain_key]["count"]
                    )
        
        # Track domain strictness
        strictness = trace.constraints_active.get("domain_strictness", 1.0)
        strictness_bucket = "strict" if strictness > 1.0 else "normal" if strictness == 1.0 else "lenient"
        domain_strictness_distribution[strictness_bucket] = domain_strictness_distribution.get(strictness_bucket, 0) + 1
    
    # Calculate average penalty
    if ideas_with_penalties > 0:
        penalty_impact_stats["average_penalty_impact"] = round(total_penalty / ideas_with_penalties, 1)
    
    penalty_impact_stats["total_ideas_with_penalties"] = ideas_with_penalties
    penalty_impact_stats["sources_affected"] = len(bias_impact_by_source)
    
    # Calculate rejected ideas count
    rejected_verdicts = AdminVerdict.query.filter(AdminVerdict.verdict == "rejected").count()
    downgraded_verdicts = AdminVerdict.query.filter(AdminVerdict.verdict == "downgraded").count()
    validated_verdicts = AdminVerdict.query.filter(AdminVerdict.verdict == "validated").count()
    
    return jsonify({
        "bias_impact_by_source": {
            domain: {
                "count": stats["count"],
                "average_penalty_percent": round(stats["avg_penalty"], 1),
                "total_penalty_sum": stats["total_penalty"]
            }
            for domain, stats in bias_impact_by_source.items()
        },
        "domain_strictness_distribution": domain_strictness_distribution,
        "penalty_impact_stats": penalty_impact_stats,
        "admin_verdicts": {
            "rejected": rejected_verdicts,
            "downgraded": downgraded_verdicts,
            "validated": validated_verdicts,
            "total": rejected_verdicts + downgraded_verdicts + validated_verdicts
        },
        "bias_transparency_summary": {
            "total_generation_traces": len(traces),
            "traces_with_active_constraints": sum(1 for t in traces if t.constraints_active),
            "average_constraint_complexity": round(
                sum(len(t.constraints_active.get("source_penalties", {})) for t in traces if t.constraints_active) / max(1, len(traces)),
                2
            )
        }
    }), 200
