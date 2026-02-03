import os
import re
import jwt
import bcrypt
import logging
from datetime import datetime
from dotenv import load_dotenv

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func
from sqlalchemy.engine.url import make_url

from backend.db import db
from backend.auth import create_access_token
from backend.ai_registry import get_active_ai_pipeline_version
from backend.retrieval.orchestrator import retrieve_sources
from backend.api.novelty import novelty_bp
from backend.models import (
    Domain,
    DomainCategory,
    ProjectIdea,
    IdeaRequest,
    IdeaReview,
    IdeaSource,
    IdeaFeedback,
    AdminVerdict,
)
from backend.health.startup_checks import run_startup_checks

# ------------------------------------------------------------------
# Environment & Config
# ------------------------------------------------------------------

load_dotenv()

from backend.config import Config  # noqa: E402

DATABASE_URL = Config.DATABASE_URL or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Set it in .env or backend/config.py before starting the app."
    )

# ------------------------------------------------------------------
# Flask App Init
# ------------------------------------------------------------------

app = Flask(__name__)

app.config.update(
    SQLALCHEMY_DATABASE_URI=DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=Config.SECRET_KEY,
)

# ------------------------------------------------------------------
# SQLAlchemy Engine Options (Neon-safe)
# ------------------------------------------------------------------

engine_opts = {}
try:
    url = make_url(DATABASE_URL)
    if url.drivername.startswith("postgresql"):
        host = url.host or ""
        is_neon_pooler = "neon.tech" in host and "pooler" in host
        if not is_neon_pooler:
            engine_opts = {
                "pool_pre_ping": True,
                "connect_args": {"options": "-c statement_timeout=5000"},
            }
        else:
            engine_opts = {"pool_pre_ping": True}
except Exception:
    engine_opts = {}

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_opts

# ------------------------------------------------------------------
# Extensions
# ------------------------------------------------------------------

db.init_app(app)

CORS(
    app,
    origins=Config.get_cors_origins(),
    supports_credentials=True,
)

logging.basicConfig(
    level=Config.LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

Config.log_config_startup()
run_startup_checks()

# ------------------------------------------------------------------
# Blueprints
# ------------------------------------------------------------------

app.register_blueprint(novelty_bp)

# ------------------------------------------------------------------
# User Model (must stay here)
# ------------------------------------------------------------------

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    preferred_domains = db.Column(db.JSON, default=list)
    skill_level = db.Column(db.String(20), default="beginner")
    saved_ideas = db.Column(db.JSON, default=list)

    preferred_domain_id = db.Column(
        db.Integer, db.ForeignKey("domains.id"), nullable=True
    )

# ------------------------------------------------------------------
# Auth / Helpers
# ------------------------------------------------------------------

def require_admin():
    claims = get_jwt()
    return claims.get("role") == "admin"


def get_current_user_id():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(
            token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGO]
        )
        return int(payload.get("sub"))
    except jwt.InvalidTokenError:
        return None

# ------------------------------------------------------------------
# Serializers
# ------------------------------------------------------------------

def serialize_public_idea(idea):
    return {
        "id": idea.id,
        "title": idea.title,
        "problem_statement": idea.problem_statement,
        "tech_stack": idea.tech_stack,
        "domain": idea.domain.name if idea.domain else None,
    }


def serialize_full_idea(idea):
    data = serialize_public_idea(idea)
    data.update(
        {
            "ai_pipeline_version": idea.ai_pipeline_version,
            "is_ai_generated": idea.is_ai_generated,
            "is_public": idea.is_public,
            "created_at": idea.created_at.isoformat(),
            "sources": [
                {
                    "source_type": s.source_type,
                    "title": s.title,
                    "url": s.url,
                    "published_date": s.published_date.isoformat()
                    if s.published_date
                    else None,
                    "summary": s.summary,
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
            "quality_score": idea.quality_score,
            "novelty_confidence": idea.novelty_confidence,
            "evidence_strength": idea.evidence_strength,
            "admin_verdict": idea.admin_verdict.verdict if idea.admin_verdict else None,
            "warning": "This idea is experimental and under review." if idea.admin_verdict and idea.admin_verdict.verdict == "rejected" else None,
        }
    )
    return data

# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# ------------------------------------------------------------------
# Legacy AI (Dead)
# ------------------------------------------------------------------

@app.route("/api/check_novelty", methods=["POST"])
def legacy_novelty():
    return jsonify({"error": "Legacy novelty scoring deprecated"}), 410


@app.route("/api/generate-idea", methods=["POST"])
def legacy_generation():
    return jsonify({"error": "Legacy AI pipeline deprecated"}), 410

# ------------------------------------------------------------------
# Platform APIs
# ------------------------------------------------------------------

@app.route("/api/ai/pipeline-version", methods=["GET"])
def pipeline_version():
    return jsonify({"version": get_active_ai_pipeline_version()}), 200


@app.route("/api/domains", methods=["GET"])
def domains():
    return jsonify({"domains": [d.to_dict() for d in Domain.query.all()]}), 200

# ------------------------------------------------------------------
# Retrieval
# ------------------------------------------------------------------

@app.route("/api/retrieval/sources", methods=["POST"])
@jwt_required()
def retrieval():
    data = request.get_json() or {}
    query = data.get("query")
    domain_id = data.get("domain_id")

    if not query or not domain_id:
        return jsonify({"error": "query and domain_id required"}), 400

    domain = Domain.query.get(domain_id)
    if not domain:
        return jsonify({"error": "Invalid domain_id"}), 400

    result = retrieve_sources(
        query=query,
        domain=domain.name,
        semantic_filter=data.get("semantic_filter", False),
        similarity_threshold=data.get("similarity_threshold", 0.6),
    )
    return jsonify(result), 200

# ------------------------------------------------------------------
# Admin Analytics (Fixed)
# ------------------------------------------------------------------

@app.route("/api/analytics/admin/domains", methods=["GET"])
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
    )


# ------------------------------------------------------------------
# Public Idea Exposure (Segment 3.1) - Anonymous, DB-only
# ------------------------------------------------------------------

@app.route("/api/public/ideas", methods=["GET"])
def public_ideas():
    query = (
        ProjectIdea.query
        .outerjoin(AdminVerdict)
        .filter(
            ProjectIdea.is_public.is_(True),
            db.or_(
                AdminVerdict.verdict.is_(None),
                AdminVerdict.verdict != "rejected"
            )
        )
    )

    ideas = query.order_by(ProjectIdea.created_at.desc()).all()

    return jsonify({
        "ideas": [
            {
                "id": i.id,
                "title": i.title,
                "problem_statement": i.problem_statement,
                "tech_stack": i.tech_stack,
                "domain": i.domain.name if i.domain else None,
            }
            for i in ideas
        ]
    }), 200


# ------------------------------------------------------------------
# Authenticated Idea Generation (Segment 3.1)
# ------------------------------------------------------------------

@app.route("/api/ideas/generate", methods=["POST"])
@jwt_required()
def generate_idea():
    """
    Evidence-anchored idea generation for authenticated users.
    Imports generation module ONLY here for structural safety.
    """
    from backend.generation.generator import generate_idea as do_generate

    data = request.get_json() or {}
    query = data.get('query')
    domain_id = data.get('domain_id')

    if not query or not domain_id:
        return jsonify({"error": "query and domain_id required"}), 400

    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    result = do_generate(query, domain_id, user_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 201


# ------------------------------------------------------------------
# Human-in-the-Loop (HITL) Refinement (Segment 3.2)
# ------------------------------------------------------------------

@app.route("/api/ideas/<int:idea_id>/feedback", methods=["POST"])
@jwt_required()
def submit_idea_feedback(idea_id):
    """
    Submit structured feedback on idea quality (Segment 3.2).
    Enforces one feedback per user per idea per type.
    """
    data = request.get_json() or {}
    feedback_type = data.get("feedback_type")
    comment = data.get("comment", "").strip()

    if feedback_type not in ["factual_error", "hallucinated_source", "weak_novelty", "poor_justification", "unclear_scope", "high_quality"]:
        return jsonify({"error": "Invalid feedback_type"}), 400

    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    # Check for existing feedback (unique constraint)
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
    db.session.commit()

    return jsonify({"message": "Feedback submitted successfully"}), 201


@app.route("/api/admin/ideas/quality-review", methods=["GET"])
@jwt_required()
def admin_quality_review():
    """
    Admin review queue for ideas needing governance (Segment 3.2).
    Returns ideas with low quality signals for admin validation.
    """
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    # Query ideas with quality issues
    ideas = ProjectIdea.query.filter(
        db.or_(
            ProjectIdea.id.in_(
                db.session.query(IdeaFeedback.idea_id).filter(
                    db.or_(
                        IdeaFeedback.feedback_type == "hallucinated_source",
                        IdeaFeedback.feedback_type == "weak_novelty"
                    )
                ).group_by(IdeaFeedback.idea_id).having(func.count() >= 1)
            ),
            # Low evidence strength (computed property, so we use source count as proxy)
            ProjectIdea.id.in_(
                db.session.query(IdeaSource.idea_id).group_by(IdeaSource.idea_id).having(func.count() < 3)
            )
        )
    ).all()

    result = []
    for idea in ideas:
        feedback_breakdown = {}
        for fb in idea.feedbacks:
            feedback_breakdown[fb.feedback_type] = feedback_breakdown.get(fb.feedback_type, 0) + 1

        result.append({
            "idea_id": idea.id,
            "title": idea.title,
            "novelty_score": None,  # Would need to compute or store
            "evidence_strength": idea.evidence_strength,
            "feedback_breakdown": feedback_breakdown,
            "source_count": len(idea.sources),
            "sources": [{"type": s.source_type, "title": s.title, "url": s.url} for s in idea.sources[:5]]
        })

    return jsonify({"review_queue": result}), 200


@app.route("/api/admin/ideas/<int:idea_id>/verdict", methods=["POST"])
@jwt_required()
def admin_verdict(idea_id):
    if not require_admin():
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}
    verdict = data.get("verdict")
    reason = data.get("reason", "").strip()

    if verdict not in ("validated", "downgraded", "rejected"):
        return jsonify({"error": "Invalid verdict"}), 400

    if not reason:
        return jsonify({"error": "Reason required"}), 400

    idea = ProjectIdea.query.get(idea_id)
    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    if idea.admin_verdict:
        return jsonify({"error": "Verdict already exists"}), 409

    if verdict == "validated":
        idea.is_validated = True
    else:
        idea.is_validated = False

    db.session.add(AdminVerdict(
        idea_id=idea_id,
        admin_id=get_current_user_id(),
        verdict=verdict,
        reason=reason,
    ))

    db.session.commit()
    return jsonify({"message": f"Idea {verdict}"}), 200

# ------------------------------------------------------------------
# Entry
# ------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
