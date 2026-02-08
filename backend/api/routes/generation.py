"""
Idea generation endpoints
"""
from functools import wraps
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.core.app import limiter
from backend.utils import require_admin, get_current_user_id


generation_bp = Blueprint("generation", __name__)


def admin_bypass_limit(limit_str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(__name__)
            # Log incoming request details to help diagnose validation errors
            try:
                body = request.get_data(as_text=True)
            except Exception:
                body = "<unreadable>"
            headers = dict(list(request.headers)[:10])
            logger.debug("admin_bypass_limit invoked for path=%s method=%s headers=%s body=%s", request.path, request.method, headers, (body[:2000] if body else ""))

            if require_admin():
                logger.debug("Admin user detected - bypassing rate limit")
                return func(*args, **kwargs)

            wrapped = limiter.limit(limit_str)(func)
            logger.debug("Calling wrapped function via limiter: %s", getattr(wrapped, '__name__', str(wrapped)))
            return wrapped(*args, **kwargs)
        return wrapper
    return decorator


@generation_bp.route("/api/ideas/generate", methods=["POST"])
@generation_bp.route("/api/ideas/generate_test", methods=["POST"])
def generate_idea():
    """Test endpoint with NO decorators"""
    return jsonify({"unique_id": "TEST_ENDPOINT_12345", "endpoint": "reached"}), 200


@generation_bp.route("/api/ideas/generate_only_jwt", methods=["POST"])
@jwt_required()
def generate_only_jwt():
    logger = logging.getLogger(__name__)
    try:
        raw = request.get_data(as_text=True)
    except Exception:
        raw = "<unreadable>"
    headers = dict(list(request.headers)[:20])
    logger.debug("ENTER generate_only_jwt headers=%s body=%s", headers, raw[:1000])
    return jsonify({"ok": "only_jwt"}), 200


@generation_bp.route("/api/ideas/generate_only_limiter", methods=["POST"])
@admin_bypass_limit("20/hour")
def generate_only_limiter():
    logger = logging.getLogger(__name__)
    try:
        raw = request.get_data(as_text=True)
    except Exception:
        raw = "<unreadable>"
    headers = dict(list(request.headers)[:20])
    logger.debug("ENTER generate_only_limiter headers=%s body=%s", headers, raw[:1000])
    return jsonify({"ok": "only_limiter"}), 200


@generation_bp.route("/api/ideas/generate_real", methods=["POST"])
@jwt_required()
@admin_bypass_limit("20/hour")
def generate_idea_real():

    """Real generation route with detailed logging for debugging 422 failures."""
    logger = logging.getLogger(__name__)
    try:
        raw = request.get_data(as_text=True)
    except Exception:
        raw = "<unreadable>"
    headers = dict(list(request.headers)[:20])
    logger.debug("ENTER generate_idea_real path=%s method=%s headers=%s body=%s", request.path, request.method, headers, raw[:5000])

    # Try to parse JSON silently so we can log raw body if parsing fails
    data = request.get_json(silent=True)
    logger.debug("Parsed JSON (silent): %s", data)

    # Determine subject (accept 'subject' or 'query')
    subject = None
    if isinstance(data, dict):
        if 'subject' in data:
            subject = data.get('subject')
        elif 'query' in data:
            subject = data.get('query')

    logger.debug("Determined subject type=%s value=%r", type(subject).__name__ if subject is not None else None, subject)

    # Validate manually to capture detailed log if invalid
    if not isinstance(subject, str) or not subject.strip():
        logger.error("Subject validation failed. raw=%r parsed=%r", raw, data)
        return jsonify({"msg": "Subject must be a string"}), 422

    domain_id = data.get('domain_id') if isinstance(data, dict) else None
    user_id = get_current_user_id()
    logger.debug("Calling generation: subject(len=%d) domain_id=%r user_id=%r", len(subject), domain_id, user_id)

    try:
        from backend.generation.generator import generate_idea as do_generate
        result = do_generate(subject, domain_id, user_id)
        logger.debug("Generation result (truncated): %s", str(result)[:2000])
        if 'error' in result:
            return jsonify(result), 400
        return jsonify(result), 201
    except Exception as e:
        logger.exception("Unhandled exception in generation")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
