"""
Public/unauthenticated endpoints
"""
from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func
from backend.core.db import db
from backend.core.app import cache
from backend.core.models import ProjectIdea, Domain, AdminVerdict, IdeaView
from backend.core.app import User


from backend.utils.serializers import serialize_public_idea

public_bp = Blueprint("public", __name__)



@public_bp.route("/api/public/ideas", methods=["GET"])
@cache.cached(timeout=300, query_string=True)
def public_ideas():
    """
    Logged-out idea browsing (DB-only).
    """
    domain = request.args.get("domain")
    q = request.args.get("q")

    if q and len(q) > 1000:
        return jsonify({"error": "Search query too long (maximum 1000 characters)"}), 400

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

    if domain:
        query = query.join(Domain).filter(Domain.name == domain)

    if q:
        ilike = f"%{q.lower()}%"
        query = query.filter(
            db.or_(
                func.lower(ProjectIdea.title).ilike(ilike),
                func.lower(ProjectIdea.problem_statement).ilike(ilike),
                func.lower(ProjectIdea.tech_stack).ilike(ilike),
            )
        )

    try:
        page = max(int(request.args.get("page", 1)), 1)
        limit = min(int(request.args.get("limit", 12)), 50)
    except ValueError:
        return jsonify({"error": "page and limit must be valid integers"}), 400

    total = query.count()

    ideas = (
        query
        .order_by(ProjectIdea.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return jsonify({
        "ideas": [
            {
                "id": i.id,
                "title": i.title,
                "problem_statement": i.problem_statement,
                "tech_stack": i.tech_stack,
                "domain": i.domain.name if i.domain else None,
                "created_at": i.created_at.isoformat(),
            }
            for i in ideas
        ],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        }
    }), 200


@public_bp.route("/api/public/ideas/<int:idea_id>", methods=["GET"])
def public_idea_detail(idea_id):
    """
    Public endpoint to view individual idea details.
    """
    idea = (
        ProjectIdea.query
        .outerjoin(AdminVerdict)
        .filter(
            ProjectIdea.id == idea_id,
            ProjectIdea.is_public.is_(True),
            db.or_(
                AdminVerdict.verdict.is_(None),
                AdminVerdict.verdict != "rejected"
            )
        )
        .first()
    )

    if not idea:
        return jsonify({"error": "Idea not found"}), 404

    user_id = get_jwt_identity()

    if user_id:
        already_viewed = IdeaView.query.filter(
            IdeaView.idea_id == idea.id,
            IdeaView.user_id == user_id
        ).first()

        if not already_viewed:
            idea.view_count += 1
            db.session.add(
                IdeaView(idea_id=idea.id, user_id=user_id)
            )
            db.session.commit()
    else:
        viewed = session.get("viewed_idea_ids", set())
        viewed = set(viewed)

        if idea.id not in viewed:
            idea.view_count += 1
            viewed.add(idea.id)
            session["viewed_idea_ids"] = list(viewed)
            db.session.commit()

    return jsonify({
        "idea": {
            "id": idea.id,
            "title": idea.title,
            "problem_statement": idea.problem_statement,
            "tech_stack": idea.tech_stack,
            "domain": idea.domain.name if idea.domain else None,
            "view_count": idea.view_count,
            "created_at": idea.created_at.isoformat(),
            "sources": [
                {
                    "source_type": s.source_type,
                    "title": s.title,
                    "url": s.url,
                    "summary": s.summary,
                }
                for s in idea.sources
            ],
        }
    }), 200


@public_bp.route("/api/public/top-ideas", methods=["GET"])
@cache.cached()
def public_top_ideas():
    ideas = (
        ProjectIdea.query
        .outerjoin(AdminVerdict)
        .filter(
            ProjectIdea.is_public.is_(True),
            db.or_(
                AdminVerdict.verdict.is_(None),
                AdminVerdict.verdict != "rejected"
            )
        )
        .order_by(ProjectIdea.view_count.desc())
        .limit(50)
        .all()
    )

    ideas = sorted(
        ideas,
        key=lambda i: (i.quality_score_cached, i.view_count),
        reverse=True
    )[:10]

    return jsonify({
        "ideas": [
            {
                "id": i.id,
                "title": i.title,
                "problem_statement": i.problem_statement,
                "tech_stack": i.tech_stack,
                "domain": i.domain.name if i.domain else None,
                "view_count": i.view_count,
            }
            for i in ideas
        ]
    }), 200


@public_bp.route("/api/public/top-domains", methods=["GET"])
@cache.cached()
def public_top_domains():
    rows = (
        db.session.query(
            Domain.name.label("domain"),
            func.count(ProjectIdea.id).label("idea_count"),
            func.coalesce(func.sum(ProjectIdea.view_count), 0).label("views")
        )
        .join(ProjectIdea)
        .outerjoin(AdminVerdict)
        .filter(
            ProjectIdea.is_public.is_(True),
            db.or_(
                AdminVerdict.verdict.is_(None),
                AdminVerdict.verdict != "rejected"
            )
        )
        .group_by(Domain.id)
        .order_by(func.count(ProjectIdea.id).desc())
        .limit(10)
        .all()
    )

    return jsonify({
        "domains": [
            {
                "domain": r.domain,
                "idea_count": int(r.idea_count),
                "views": int(r.views),
            }
            for r in rows
        ]
    }), 200


@public_bp.route("/api/public/stats", methods=["GET"])
@cache.cached()
def public_stats():
    total_public_ideas = (
        ProjectIdea.query
        .outerjoin(AdminVerdict)
        .filter(
            ProjectIdea.is_public.is_(True),
            db.or_(
                AdminVerdict.verdict.is_(None),
                AdminVerdict.verdict != "rejected"
            )
        )
        .count()
    )

    return jsonify({
        "total_public_ideas": total_public_ideas,
        "total_domains": Domain.query.count(),
    }), 200
