import os

import pytest
import requests

BASE_URL = os.getenv("TEST_API_BASE_URL", "http://localhost:5000")


def _api_is_live() -> bool:
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def _login() -> str | None:
    email = os.getenv("TEST_USER_EMAIL", "test@test.com")
    password = os.getenv("TEST_USER_PASSWORD", "TestUser@123")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception:
        return None
    return None


@pytest.fixture(scope="module", autouse=True)
def require_live_api():
    if not _api_is_live():
        pytest.skip(f"Live API not running at {BASE_URL}")


def test_public_ideas_list():
    resp = requests.get(f"{BASE_URL}/api/public/ideas", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert "ideas" in data


def test_generate_requires_auth():
    resp = requests.post(
        f"{BASE_URL}/api/ideas/generate",
        json={"subject": "Test idea", "domain_id": 1},
        timeout=15,
    )
    assert resp.status_code in (401, 422)


def test_generate_with_auth():
    token = _login()
    if not token:
        pytest.skip("Test user credentials not available")

    resp = requests.post(
        f"{BASE_URL}/api/ideas/generate",
        json={"subject": "AI tool for code review", "domain_id": 1},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert resp.status_code in (200, 201, 202)
    data = resp.json()
    assert "status" in data or "job_id" in data
