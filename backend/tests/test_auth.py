"""Unit tests for backend.auth module."""
import time
import pytest
from unittest.mock import patch, MagicMock
from backend.auth import create_access_token, jwt_required
from backend.config import Config


def test_create_access_token():
    """Test that create_access_token generates a valid JWT."""
    user_id = 1
    role = "user"
    token = create_access_token(user_id=user_id, role=role)

    # Decode the token to verify its contents
    import jwt
    payload = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGO])

    assert payload["sub"] == str(user_id)
    assert payload["role"] == role
    assert "exp" in payload
    assert payload["exp"] > time.time()


def test_jwt_required_missing_header():
    """Test jwt_required decorator with missing Authorization header."""
    from flask import Flask, request

    app = Flask(__name__)

    @app.route('/test')
    @jwt_required()
    def test_route():
        return "success"

    with app.test_client() as client:
        response = client.get('/test')
        assert response.status_code == 401
        assert b"Missing or invalid Authorization header" in response.data


def test_jwt_required_invalid_token():
    """Test jwt_required decorator with invalid token."""
    from flask import Flask

    app = Flask(__name__)

    @app.route('/test')
    @jwt_required()
    def test_route():
        return "success"

    with app.test_client() as client:
        response = client.get('/test', headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401
        assert b"Invalid token" in response.data


def test_jwt_required_expired_token():
    """Test jwt_required decorator with expired token."""
    from flask import Flask

    # Create an expired token
    import jwt
    expired_payload = {
        "sub": 1,
        "role": "user",
        "exp": time.time() - 100  # Expired 100 seconds ago
    }
    expired_token = jwt.encode(expired_payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGO)

    app = Flask(__name__)

    @app.route('/test')
    @jwt_required()
    def test_route():
        return "success"

    with app.test_client() as client:
        response = client.get('/test', headers={"Authorization": f"Bearer {expired_token}"})
        assert response.status_code == 401
        assert b"Token expired" in response.data


def test_jwt_required_insufficient_permissions():
    """Test jwt_required decorator with insufficient permissions for admin route."""
    from flask import Flask

    # Create a user token (not admin)
    user_token = create_access_token(user_id=1, role="user")

    app = Flask(__name__)

    @app.route('/test')
    @jwt_required(required_role="admin")
    def test_route():
        return "success"

    with app.test_client() as client:
        response = client.get('/test', headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 403
        assert b"Insufficient permissions" in response.data


def test_jwt_required_admin_success():
    """Test jwt_required decorator with admin token accessing admin route."""
    from flask import Flask

    # Create an admin token
    admin_token = create_access_token(user_id=1, role="admin")

    app = Flask(__name__)

    @app.route('/test')
    @jwt_required(required_role="admin")
    def test_route():
        return "success"

    with app.test_client() as client:
        response = client.get('/test', headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        assert b"success" in response.data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
