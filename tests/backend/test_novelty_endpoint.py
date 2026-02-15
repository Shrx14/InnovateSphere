"""Tests for novelty analysis endpoint."""
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
def auth_headers(app):
    from flask_jwt_extended import create_access_token
    with app.app_context():
        token = create_access_token(
            identity=1,
            additional_claims={"role": "user", "email": "test@example.com"}
        )
        return {"Authorization": f"Bearer {token}"}


def test_check_novelty_requires_auth(client):
    """Novelty endpoint should require authentication."""
    resp = client.post('/api/check_novelty', json={"description": "test"})
    assert resp.status_code == 401


def test_check_novelty_missing_description(client, auth_headers):
    """Missing description should return 400."""
    resp = client.post('/api/check_novelty', json={}, headers=auth_headers)
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data


@patch("backend.novelty.router.route_engine")
def test_check_novelty_success(mock_route, client, auth_headers):
    """Successful novelty check with mocked engine."""
    mock_engine = MagicMock()
    mock_engine.analyze.return_value = {
        "novelty_score": 72.0,
        "novelty_level": "moderate",
        "engine": "generic",
        "debug": {},
        "sources": [],
    }
    mock_route.return_value = (mock_engine, "ai", 0.8, "general", 0.7)

    resp = client.post(
        '/api/check_novelty',
        json={"description": "Test idea about AI"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "novelty_score" in data
