"""Tests for admin endpoints: verdict updates, rescore, human-verified, hallucinated sources."""
import pytest
from unittest.mock import patch, MagicMock


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


@pytest.fixture
def admin_headers(app):
    from flask_jwt_extended import create_access_token
    with app.app_context():
        token = create_access_token(
            identity=1,
            additional_claims={"role": "admin", "email": "admin@example.com"}
        )
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers(app):
    from flask_jwt_extended import create_access_token
    with app.app_context():
        token = create_access_token(
            identity=2,
            additional_claims={"role": "user", "email": "user@example.com"}
        )
        return {"Authorization": f"Bearer {token}"}


class TestAdminVerdict:
    """Tests for POST /api/admin/ideas/<id>/verdict"""

    def test_verdict_requires_admin(self, client, user_headers):
        """Non-admin users should be rejected."""
        res = client.post(
            "/api/admin/ideas/1/verdict",
            json={"verdict": "validated", "reason": "good"},
            headers=user_headers
        )
        assert res.status_code == 403

    def test_verdict_validates_values(self, client, admin_headers):
        """Only validated/downgraded/rejected are valid verdicts."""
        res = client.post(
            "/api/admin/ideas/1/verdict",
            json={"verdict": "invalid_verdict"},
            headers=admin_headers
        )
        assert res.status_code == 400

    def test_rejected_requires_reason(self, client, admin_headers):
        """Rejected verdict must include a reason."""
        res = client.post(
            "/api/admin/ideas/1/verdict",
            json={"verdict": "rejected", "reason": ""},
            headers=admin_headers
        )
        assert res.status_code == 400


class TestAdminRescore:
    """Tests for POST /api/admin/ideas/<id>/rescore"""

    def test_rescore_requires_admin(self, client, user_headers):
        res = client.post("/api/admin/ideas/1/rescore", headers=user_headers)
        assert res.status_code == 403

    def test_rescore_returns_404_for_missing_idea(self, client, admin_headers):
        res = client.post("/api/admin/ideas/99999/rescore", headers=admin_headers)
        assert res.status_code == 404


class TestHumanVerified:
    """Tests for POST /api/admin/ideas/<id>/human-verified"""

    def test_human_verified_requires_admin(self, client, user_headers):
        res = client.post(
            "/api/admin/ideas/1/human-verified",
            json={"verified": True},
            headers=user_headers
        )
        assert res.status_code == 403

    def test_human_verified_validates_boolean(self, client, admin_headers):
        """verified must be a boolean."""
        res = client.post(
            "/api/admin/ideas/1/human-verified",
            json={"verified": "yes"},
            headers=admin_headers
        )
        assert res.status_code == 400


class TestHallucinatedSource:
    """Tests for POST /api/admin/ideas/<id>/sources/<sid>/hallucinated"""

    def test_hallucinated_requires_admin(self, client, user_headers):
        res = client.post(
            "/api/admin/ideas/1/sources/1/hallucinated",
            json={"hallucinated": True},
            headers=user_headers
        )
        assert res.status_code == 403
