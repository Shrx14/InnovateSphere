"""
Authentication endpoints (login, register, etc.)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from backend.core.db import db
from backend.core.app import User

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
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    # Determine user role from the database role column
    user_role = user.role or "user"
    # Legacy fallback: if no role column yet, check known admin email
    if user_role == "user" and user.email == "admin@example.com":
        user_role = "admin"

    # Generate JWT token with user ID and role
    token = create_access_token(
        identity=user.id,
        additional_claims={
            "role": user_role,
            "email": user.email,
            "preferred_domain_id": user.preferred_domain_id
        }
    )

    return jsonify({
        "access_token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user_role
        }
    }), 200


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    """
    Logout endpoint (optional).
    In practice, frontend just clears localStorage.
    This can be used for token blacklisting if needed.
    """
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/api/register", methods=["POST"])
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
            identity=new_user.id,
            additional_claims={
                "role": "user",
                "email": new_user.email,
                "preferred_domain_id": new_user.preferred_domain_id
            }
        )

        return jsonify({
            "access_token": token,
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
