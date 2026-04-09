import os

import pytest
import requests

BASE_URL = os.getenv("TEST_API_BASE_URL", "http://localhost:5000")
NOVELTY_URL = f"{BASE_URL}/api/novelty/analyze"


TEST_CASES = [
    {
        "name": "Personalized Health Platform",
        "description": (
            "A personalized health platform that combines data-driven fitness guidance "
            "with local community support, integrating biometric analysis, adaptive "
            "workout plans, and connections to local nutritionists and trainers."
        ),
        "domain": "Software",
    },
    {
        "name": "Data-Driven AI Analytics Platform",
        "description": (
            "A machine-learning powered analytics platform that provides real-time data "
            "insights and predictive modeling for business intelligence at scale."
        ),
        "domain": "Software",
    },
    {
        "name": "Short vague query",
        "description": "personalized health platform",
        "domain": "Software",
    },
    {
        "name": "Long detailed query",
        "description": (
            "A personalized health platform that combines data-driven fitness guidance with "
            "local community support, integrating biometric analysis and adaptive workout plans."
        ),
        "domain": "Software",
    },
    {
        "name": "Medium query",
        "description": "real time chat application platform",
        "domain": "Software",
    },
]


def _api_is_live() -> bool:
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="module", autouse=True)
def require_live_api():
    if not _api_is_live():
        pytest.skip(f"Live API not running at {BASE_URL}")


@pytest.mark.parametrize("case", TEST_CASES, ids=[c["name"] for c in TEST_CASES])
def test_novelty_analyze_live(case):
    payload = {
        "description": case["description"],
        "domain": case["domain"],
    }
    response = requests.post(NOVELTY_URL, json=payload, timeout=60)
    assert response.status_code == 200
    data = response.json()
    assert "novelty_score" in data
    assert isinstance(data.get("sources", []), list)
