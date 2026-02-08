"""
Authentication utilities for the backend.
"""
from flask_jwt_extended import get_jwt, get_jwt_identity


def require_admin():
    """
    Check if the current user has admin role.
    Returns True if admin, False otherwise.
    """
    claims = get_jwt()
    return claims.get("role") == "admin"


def get_current_user_id():
    """
    Get current user ID using Flask-JWT-Extended's get_jwt_identity().
    This standardizes JWT handling across the application.
    """
    try:
        return int(get_jwt_identity())
    except (ValueError, TypeError):
        return None
