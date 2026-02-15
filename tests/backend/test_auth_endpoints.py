"""Tests for auth endpoints: login, register, refresh, logout with blocklist."""
import pytest
from unittest.mock import patch


@pytest.fixture
def app():
    from backend.core.app import create_app
    from backend.core.db import db
    app = create_app(test_config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


class TestLogin:
    """Tests for POST /api/login"""

    def test_login_requires_email_and_password(self, client):
        res = client.post("/api/login", json={})
        assert res.status_code == 400

    def test_login_rejects_missing_email(self, client):
        res = client.post("/api/login", json={"password": "test123"})
        assert res.status_code == 400

    def test_login_rejects_missing_password(self, client):
        res = client.post("/api/login", json={"email": "test@example.com"})
        assert res.status_code == 400

    def test_login_returns_refresh_token(self, client, app):
        """Successful login should return both access_token and refresh_token."""
        from backend.core.db import db
        from backend.core.models import User
        from werkzeug.security import generate_password_hash

        with app.app_context():
            user = User(
                email="test@example.com",
                username="testuser",
                password_hash=generate_password_hash("password123"),
                role="user"
            )
            db.session.add(user)
            db.session.commit()

            res = client.post("/api/login", json={
                "email": "test@example.com",
                "password": "password123"
            })
            assert res.status_code == 200
            data = res.get_json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["user"]["email"] == "test@example.com"


class TestRegister:
    """Tests for POST /api/register"""

    def test_register_requires_fields(self, client):
        res = client.post("/api/register", json={})
        assert res.status_code == 400

    def test_register_validates_email(self, client):
        res = client.post("/api/register", json={
            "email": "invalid",
            "username": "testuser",
            "password": "password123"
        })
        assert res.status_code == 400

    def test_register_validates_password_length(self, client):
        res = client.post("/api/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "short"
        })
        assert res.status_code == 400


class TestRefresh:
    """Tests for POST /api/refresh"""

    def test_refresh_requires_refresh_token(self, client):
        """Refresh without token should fail."""
        res = client.post("/api/refresh")
        assert res.status_code == 401

    def test_refresh_rejects_access_token(self, client, app):
        """Access token should not work for refresh endpoint."""
        from flask_jwt_extended import create_access_token
        with app.app_context():
            token = create_access_token(
                identity=1,
                additional_claims={"role": "user"}
            )
            res = client.post(
                "/api/refresh",
                headers={"Authorization": f"Bearer {token}"}
            )
            # Flask-JWT-Extended returns 422 when an access token is used
            # where a refresh token is expected
            assert res.status_code in (401, 422)


class TestLogout:
    """Tests for POST /api/logout"""

    def test_logout_requires_auth(self, client):
        """Logout without token should fail."""
        res = client.post("/api/logout")
        assert res.status_code == 401

    def test_logout_succeeds_with_token(self, client, app):
        """Logout with valid token should succeed."""
        from flask_jwt_extended import create_access_token
        from backend.core.db import db

        with app.app_context():
            db.create_all()
            token = create_access_token(
                identity=1,
                additional_claims={"role": "user"}
            )
            res = client.post(
                "/api/logout",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert res.status_code == 200
            assert "Logged out" in res.get_json()["message"]


class TestNoveltyAuth:
    """Tests for POST /api/novelty/analyze auth guard"""

    def test_novelty_requires_auth(self, client):
        """Novelty endpoint should reject unauthenticated requests."""
        res = client.post(
            "/api/novelty/analyze",
            json={"description": "test", "domain": "ai"}
        )
        assert res.status_code == 401
