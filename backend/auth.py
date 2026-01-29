import time
import jwt
import logging
from functools import wraps
from flask import request, jsonify, g
from backend.config import Config

logger = logging.getLogger(__name__)


def create_access_token(user_id: int, role: str = "user", username: str = "", email: str = "") -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "username": username,
        "email": email,
        "exp": int(time.time()) + Config.JWT_EXP_SECONDS,
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGO)


def jwt_required(required_role: str | None = None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid Authorization header"}), 401

            token = auth_header.split(" ", 1)[1]
            try:
                payload = jwt.decode(
                    token,
                    Config.JWT_SECRET,
                    algorithms=[Config.JWT_ALGO],
                )
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            g.current_user_id = int(payload.get("sub"))
            g.current_user_role = payload.get("role")

            if required_role and g.current_user_role != required_role:
                return jsonify({"error": "Insufficient permissions"}), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator
