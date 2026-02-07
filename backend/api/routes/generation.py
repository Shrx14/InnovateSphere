"""
Idea generation endpoints
"""
from functools import wraps
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.core.app import limiter
from backend.utils import require_admin, get_current_user_id


generation_bp = Blueprint("generation", __name__)


def admin_bypass_limit(limit_str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if require_admin():
                return func(*args, **kwargs)
            return limiter.limit(limit_str)(func)(*args, **kwargs)
        return wrapper
    return decorator


@generation_bp.route("/api/ideas/generate", methods=["POST"])
@jwt_required()
@admin_bypass_limit("20/hour")
def generate_idea():
    """
    Evidence-anchored idea generation for authenticated users.
    """
    from backend.generation.generator import generate_idea as do_generate

    data = request.get_json() or {}
    query = data.get('query', '').strip() if data.get('query') else None
    domain_id = data.get('domain_id')

    if not query or not domain_id:
        return jsonify({"error": "query and domain_id required"}), 400

    if len(query) > 2000:
        return jsonify({"error": "query must be 2000 characters or less"}), 400

    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    result = do_generate(query, domain_id, user_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 201
