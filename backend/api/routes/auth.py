"""
Authentication endpoints (login, register, token refresh, logout with blocklist)
"""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from werkzeug.security import check_password_hash, generate_password_hash

from backend.core.db import db
from backend.core.models import User, TokenBlocklist
from backend.core.config import Config
from backend.core.app import limiter

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/login", methods=["POST"])
def login():
    """
    User login endpoint.
    Request: { "email": "user@example.com", "password": "password123" }
    Response: { "access_token": "jwt_token_here", "user": {...} }
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    # Validate input
    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    # Find user by email (case-insensitive)
    user = User.query.filter_by(email=email.lower()).first()

    # Verify user exists and password is correct
    try:
        password_valid = user and check_password_hash(user.password_hash, password)
    except (ValueError, TypeError):
        password_valid = False
    if not password_valid:
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    # Determine user role from the database role column
    user_role = user.role or "user"
    # Legacy fallback: if no role column yet, check known admin email
    if user_role == "user" and user.email == "admin@example.com":
        user_role = "admin"

    import logging as _logging
    _logging.getLogger(__name__).info(
        "[LOGIN] user_id=%s email=%s db_role=%r resolved_role=%s",
        user.id, user.email, user.role, user_role
    )

    # Generate JWT token with user ID and role
    additional_claims = {
        "role": user_role,
        "email": user.email,
        "preferred_domain_id": user.preferred_domain_id
    }
    token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={"role": user_role}
    )

    return jsonify({
        "access_token": token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user_role
        }
    }), 200


@auth_bp.route("/api/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Real logout: adds current token JTI to blocklist so it cannot be reused.
    """
    jti = get_jwt()["jti"]
    db.session.add(TokenBlocklist(jti=jti, created_at=datetime.now(timezone.utc)))
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/api/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    Token refresh endpoint.
    Request: Authorization header with refresh token.
    Response: { "access_token": "new_jwt" }
    """
    identity = get_jwt_identity()
    claims = get_jwt()
    user_role = claims.get("role", "user")

    new_token = create_access_token(
        identity=identity,
        additional_claims={"role": user_role}
    )
    return jsonify({"access_token": new_token}), 200


@auth_bp.route("/api/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    """
    User registration endpoint.
    Request: { "email": "user@example.com", "username": "username", "password": "password123", "skill_level": "beginner" }
    Response: { "access_token": "jwt_token_here", "user": {...} }
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    skill_level = data.get("skill_level", "beginner").strip()

    # Validate input
    if not email or not username or not password:
        return jsonify({
            "error": "Email, username, and password are required"
        }), 400

    # Validate email format (basic check)
    if "@" not in email or "." not in email:
        return jsonify({
            "error": "Please enter a valid email address"
        }), 400

    # Validate password length
    if len(password) < 6:
        return jsonify({
            "error": "Password must be at least 6 characters long"
        }), 400

    # Validate username length
    if len(username) < 3:
        return jsonify({
            "error": "Username must be at least 3 characters long"
        }), 400

    # Check if email already exists (case-insensitive)
    existing_email = User.query.filter_by(email=email.lower()).first()
    if existing_email:
        return jsonify({
            "error": "An account with this email already exists"
        }), 409

    # Check if username already exists (case-insensitive)
    existing_username = User.query.filter_by(username=username.lower()).first()
    if existing_username:
        return jsonify({
            "error": "This username is already taken"
        }), 409

    # Create new user
    try:
        new_user = User(
            email=email.lower(),
            username=username,
            password_hash=generate_password_hash(password),
            skill_level=skill_level
        )
        db.session.add(new_user)
        db.session.commit()

        # Generate JWT token
        token = create_access_token(
            identity=str(new_user.id),
            additional_claims={
                "role": "user",
                "email": new_user.email,
                "preferred_domain_id": new_user.preferred_domain_id
            }
        )
        refresh_token = create_refresh_token(
            identity=str(new_user.id),
            additional_claims={"role": "user"}
        )

        return jsonify({
            "access_token": token,
            "refresh_token": refresh_token,
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "username": new_user.username,
                "role": "user"
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Registration failed. Please try again."
        }), 500


@auth_bp.route("/api/user/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Get current user's profile."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "skill_level": user.skill_level,
        "preferred_domain_id": user.preferred_domain_id,
        "preferred_domains": user.preferred_domains or [],
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }), 200


@auth_bp.route("/api/user/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """Update current user's profile (username, skill_level, preferred_domain_id)."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}

    if "username" in data:
        new_username = data["username"].strip()
        if len(new_username) < 3:
            return jsonify({"error": "Username must be at least 3 characters"}), 400
        # Check uniqueness
        existing = User.query.filter(User.username == new_username, User.id != user.id).first()
        if existing:
            return jsonify({"error": "Username already taken"}), 409
        user.username = new_username

    if "skill_level" in data:
        valid_levels = ["beginner", "intermediate", "advanced", "expert"]
        if data["skill_level"] not in valid_levels:
            return jsonify({"error": f"skill_level must be one of: {', '.join(valid_levels)}"}), 400
        user.skill_level = data["skill_level"]

    if "preferred_domain_id" in data:
        user.preferred_domain_id = data["preferred_domain_id"]

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to update profile"}), 500

    return jsonify({
        "message": "Profile updated",
        "user": {
            "id": user.id,
            "username": user.username,
            "skill_level": user.skill_level,
            "preferred_domain_id": user.preferred_domain_id,
        }
    }), 200


@auth_bp.route("/api/user/password", methods=["PUT"])
@jwt_required()
def change_password():
    """Change password (requires current password)."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return jsonify({"error": "Current and new passwords are required"}), 400

    if not user.check_password(current_password):
        return jsonify({"error": "Current password is incorrect"}), 401

    if len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400

    user.set_password(new_password)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to change password"}), 500

    return jsonify({"message": "Password changed successfully"}), 200
