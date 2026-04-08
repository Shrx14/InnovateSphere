"""
Analytics endpoints (admin and user)
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, case
from backend.core.config import Config
from backend.core.db import db
from backend.core.app import cache, User
from backend.core.models import ProjectIdea, Domain, IdeaRequest, IdeaReview, IdeaFeedback, AdminVerdict, GenerationTrace
from backend.utils import require_admin, db_retry
from backend.evaluation.service import evaluate_idea_batch, get_reference_eval_index
from backend.semantic.embedder import get_embedder

analytics_bp = Blueprint("analytics", __name__)


def _build_eval_payload(idea: ProjectIdea) -> dict:
    payload = {}
    if isinstance(getattr(idea, "problem_statement_json", None), dict):
        payload.update(idea.problem_statement_json)

    payload.setdefault("title", idea.title)
    payload.setdefault("problem_statement", idea.problem_statement)

    tech_stack_json = getattr(idea, "tech_stack_json", None)
    if isinstance(tech_stack_json, list):
        payload.setdefault("tech_stack", tech_stack_json)
    else:
        payload.setdefault("tech_stack", idea.tech_stack)

    return payload


def _bucket_scores(values: list[float], bucket_size: int = 10) -> list[dict]:
    buckets = {i: 0 for i in range(0, 101, bucket_size)}
    for val in values:
        if not isinstance(val, (int, float)):
            continue
        pct = max(0.0, min(100.0, float(val) * 100.0))
        bucket = int(min(100, (pct // bucket_size) * bucket_size))
        buckets[bucket] = buckets.get(bucket, 0) + 1
    return [{"range": f"{k}-{k + bucket_size}", "count": v} for k, v in buckets.items()]


@analytics_bp.route("/api/analytics/admin/kpis", methods=["GET"])
@jwt_required()
@db_retry()
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


@analytics_bp.route("/api/analytics/admin/evaluation", methods=["GET"])
@jwt_required()
@db_retry()
def admin_evaluation_metrics():
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    try:
        limit_raw = request.args.get("limit", Config.EVAL_ANALYTICS_MAX_IDEAS)
        limit = min(int(limit_raw), Config.EVAL_ANALYTICS_MAX_IDEAS)
    except Exception:
        limit = Config.EVAL_ANALYTICS_MAX_IDEAS

    ideas = (
        ProjectIdea.query
        .order_by(ProjectIdea.created_at.desc())
        .limit(limit)
        .all()
    )

    payloads = [_build_eval_payload(idea) for idea in ideas]
    if not payloads:
        return jsonify({
            "aggregate": {
                "ins_mean": None,
                "cs_mean": None,
                "ids": 0.0,
                "rr": 0.0,
                "idea_count": 0,
                "reference_index_loaded": False,
                "sample_size": 0,
            },
            "distributions": {
                "ins": [],
                "cs": [],
            }
        }), 200

    reference_index = get_reference_eval_index()
    embedder = get_embedder()

    eval_results = evaluate_idea_batch(
        payloads,
        reference_index=reference_index,
        k=max(1, getattr(Config, "EVAL_REFERENCE_NEIGHBORS", 5)),
        embedder=embedder,
    )

    per_idea = eval_results.get("per_idea", [])
    ins_values = [row.get("ins") for row in per_idea if isinstance(row.get("ins"), float)]
    cs_values = [row.get("cs") for row in per_idea if isinstance(row.get("cs"), float)]

    aggregate = eval_results.get("aggregate", {})
    aggregate["reference_index_loaded"] = reference_index is not None
    aggregate["sample_size"] = len(payloads)

    return jsonify({
        "aggregate": aggregate,
        "distributions": {
            "ins": _bucket_scores(ins_values),
            "cs": _bucket_scores(cs_values),
        }
    }), 200




# ============================================================================
# Frontend-facing admin analytics endpoints (at /api/admin/... routes)
# ============================================================================

@analytics_bp.route("/api/admin/domains", methods=["GET"])
@jwt_required()
@db_retry()
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

    from datetime import datetime, timedelta, timezone

    # Get last 30 days of data
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

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

    # Use SQL aggregation instead of loading all ideas into memory
    bucket_size = 10

    def _histogram_query(score_col):
        bucket_expr = func.least(func.floor(func.coalesce(score_col, 0) / bucket_size) * bucket_size, 100)
        rows = (
            db.session.query(
                bucket_expr.label("bucket"),
                func.count().label("cnt"),
            )
            .group_by(bucket_expr)
            .all()
        )
        buckets = {i: 0 for i in range(0, 101, bucket_size)}
        for row in rows:
            b = int(row.bucket)
            if b in buckets:
                buckets[b] = row.cnt
        return [{"range": f"{k}-{k + bucket_size}", "count": v} for k, v in buckets.items()]

    return jsonify({
        "novelty": _histogram_query(ProjectIdea.novelty_score_cached),
        "quality": _histogram_query(ProjectIdea.quality_score_cached),
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
    
    try:
        from backend.core.models import GenerationTrace
        from backend.core.db import db
        
        # Use db.session.query() because GenerationTrace has a column named 'query'
        # which shadows the default Model.query class attribute.
        total_traces = db.session.query(GenerationTrace).count()
        traces_with_constraints = (
            db.session.query(GenerationTrace).filter(GenerationTrace.constraints_active.isnot(None)).count()
        )

        # Only load traces that actually have constraints for detailed analysis
        constrained_traces = (
            db.session.query(GenerationTrace)
            .filter(GenerationTrace.constraints_active.isnot(None))
            .limit(5000)
            .all()
        )

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
        total_constraint_complexity = 0
        
        for trace in constrained_traces:
            
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

            # Accumulate constraint complexity for average
            total_constraint_complexity += len(source_penalties)
        
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
                "total_generation_traces": total_traces,
                "traces_with_active_constraints": traces_with_constraints,
                "average_constraint_complexity": round(
                    total_constraint_complexity / max(1, len(constrained_traces)),
                    2
                )
            }
        }), 200

    except Exception as e:
        import logging, traceback
        logging.getLogger(__name__).exception("bias-transparency endpoint failed")
        return jsonify({
            "error": "Bias transparency query failed",
            "details": str(e)
        }), 500
