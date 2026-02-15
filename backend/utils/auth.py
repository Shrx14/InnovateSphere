"""
Authentication utilities for the backend.
"""
import logging
from flask_jwt_extended import get_jwt, get_jwt_identity

_logger = logging.getLogger(__name__)


def require_admin():
    """
    Check if the current user has admin role.
    Returns True if admin, False otherwise.
    """
    claims = get_jwt()
    is_admin = claims.get("role") == "admin"
    if not is_admin:
        _logger.warning(
            "[AUTH] require_admin DENIED — jwt sub=%s role=%r (expected 'admin')",
            claims.get("sub"), claims.get("role"),
        )
    return is_admin


def get_current_user_id():
    """
    Get current user ID using Flask-JWT-Extended's get_jwt_identity().
    This standardizes JWT handling across the application.
    """
    try:
        return int(get_jwt_identity())
    except (ValueError, TypeError):
        return None
