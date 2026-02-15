"""Tests for ideas routes: reviews, feedback, and list endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


@pytest.fixture
def app():
    """Create a test Flask app with all blueprints."""
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


@pytest.fixture
def auth_headers(app):
    """Generate valid JWT auth headers for testing."""
    from flask_jwt_extended import create_access_token
    with app.app_context():
        token = create_access_token(
            identity=1,
            additional_claims={"role": "user", "email": "test@example.com"}
        )
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(app):
    """Generate valid JWT auth headers for admin testing."""
    from flask_jwt_extended import create_access_token
    with app.app_context():
        token = create_access_token(
            identity=1,
            additional_claims={"role": "admin", "email": "admin@example.com"}
        )
        return {"Authorization": f"Bearer {token}"}


class TestReviewEndpoint:
    """Tests for POST /api/ideas/<id>/review"""

    def test_review_requires_auth(self, client):
        """Review endpoint should reject unauthenticated requests."""
        res = client.post("/api/ideas/1/review", json={"rating": 5})
        assert res.status_code == 401

    def test_review_validates_rating_range(self, client, auth_headers):
        """Rating must be between 1 and 5."""
        res = client.post(
            "/api/ideas/1/review",
            json={"rating": 0},
            headers=auth_headers
        )
        assert res.status_code == 400
        assert "Rating must be" in res.get_json()["error"]

        res = client.post(
            "/api/ideas/1/review",
            json={"rating": 6},
            headers=auth_headers
        )
        assert res.status_code == 400

    def test_review_validates_rating_type(self, client, auth_headers):
        """Rating must be an integer."""
        res = client.post(
            "/api/ideas/1/review",
            json={"rating": "five"},
            headers=auth_headers
        )
        assert res.status_code == 400

    def test_review_rejects_long_comment(self, client, auth_headers):
        """Comment must be under 5000 chars."""
        res = client.post(
            "/api/ideas/1/review",
            json={"rating": 4, "comment": "x" * 5001},
            headers=auth_headers
        )
        assert res.status_code == 400


class TestFeedbackEndpoint:
    """Tests for POST /api/ideas/<id>/feedback"""

    def test_feedback_requires_auth(self, client):
        """Feedback endpoint should reject unauthenticated requests."""
        res = client.post(
            "/api/ideas/1/feedback",
            json={"feedback_type": "high_quality"}
        )
        assert res.status_code == 401

    def test_feedback_rejects_invalid_type(self, client, auth_headers):
        """Invalid feedback_type should be rejected."""
        res = client.post(
            "/api/ideas/1/feedback",
            json={"feedback_type": "invalid_type"},
            headers=auth_headers
        )
        assert res.status_code == 400

    def test_feedback_accepts_valid_types(self, client, auth_headers):
        """All valid feedback types should be accepted (if idea exists)."""
        valid_types = [
            "factual_error", "hallucinated_source", "weak_novelty",
            "poor_justification", "unclear_scope", "high_quality"
        ]
        for ft in valid_types:
            # Will return 404 (idea not found) but NOT 400 (invalid type)
            res = client.post(
                "/api/ideas/999/feedback",
                json={"feedback_type": ft},
                headers=auth_headers
            )
            assert res.status_code in (201, 404, 409), \
                f"Unexpected status {res.status_code} for feedback_type={ft}"


class TestListEndpoints:
    """Tests for GET list endpoints."""

    def test_reviews_list_requires_auth(self, client):
        res = client.get("/api/ideas/1/reviews")
        assert res.status_code == 401

    def test_feedbacks_list_requires_auth(self, client):
        res = client.get("/api/ideas/1/feedbacks")
        assert res.status_code == 401

    def test_my_ideas_requires_auth(self, client):
        res = client.get("/api/ideas/mine")
        assert res.status_code == 401
