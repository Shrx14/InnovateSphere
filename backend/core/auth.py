import time
import jwt
import logging
from functools import wraps
from flask import request, jsonify, g
from backend.core.config import Config

logger = logging.getLogger(__name__)


def create_access_token(*args, **kwargs) -> str:
    """Compatibility wrapper for token creation.

    Accepts either the project's (user_id, role) signature or the
    flask-jwt-extended style `identity` / `additional_claims` kwargs used
    by tests.
    """
    # Support flask-jwt-extended style
    if 'identity' in kwargs:
        user_id = kwargs.get('identity')
        additional = kwargs.get('additional_claims', {}) or {}
        role = additional.get('role', kwargs.get('role', 'user'))
    else:
        # Support legacy signature create_access_token(user_id=..., role=...)
        user_id = kwargs.get('user_id') if 'user_id' in kwargs else (args[0] if args else None)
        role = kwargs.get('role', args[1] if len(args) > 1 else 'user')

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": int(time.time()) + Config.JWT_EXP_SECONDS,
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGO)


def get_jwt():
    """Return decoded JWT claims for the current request, if any."""
    return getattr(g, '_jwt_claims', None) or {}


def jwt_required(required_role: str = None):
    """Simple decorator enforcing presence of a valid JWT and optional role."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            auth = request.headers.get('Authorization', '')
            if not auth.startswith('Bearer '):
                return jsonify({'msg': 'Missing Authorization header'}), 401
            token = auth.split(' ', 1)[1]
            try:
                claims = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGO])
            except jwt.ExpiredSignatureError:
                return jsonify({'msg': 'Token expired'}), 401
            except Exception:
                return jsonify({'msg': 'Invalid token'}), 401

            # store claims for get_jwt()
            g._jwt_claims = claims

            if required_role and claims.get('role') != required_role:
                return jsonify({'error': 'Insufficient permissions'}), 403

            return fn(*a, **kw)

        return wrapper

    return decorator
