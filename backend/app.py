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
)

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
    """
    Anonymous access to validated public ideas.
    Pure DB query, limited fields.
    """
    keyword = request.args.get('q', '')
    domain_id = request.args.get('domain_id')
    sort_by = request.args.get('sort', 'popularity')  # popularity or recency

    query = ProjectIdea.query.filter_by(is_public=True, is_validated=True)

    if domain_id:
        query = query.filter_by(domain_id=int(domain_id))

    if keyword:
        query = query.filter(ProjectIdea.title.ilike(f'%{keyword}%'))

    if sort_by == 'popularity':
        # Sort by request count desc
        query = query.outerjoin(IdeaRequest).group_by(ProjectIdea.id).order_by(func.count(IdeaRequest.id).desc())
    else:
        # Recency
        query = query.order_by(ProjectIdea.created_at.desc())

    ideas = query.all()

    return jsonify({
        "ideas": [serialize_public_idea(idea) for idea in ideas],
        "login_required_for": [
            "full description",
            "evidence",
            "novelty analysis",
            "custom idea generation"
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
# Entry
# ------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
