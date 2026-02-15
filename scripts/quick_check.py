"""Quick check of previously-failing routes."""
import requests

BASE = "http://localhost:5000"

r = requests.post(f"{BASE}/api/login", json={"email": "test@example.com", "password": "AdminPass123"}, timeout=10)
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

routes = [
    "/api/admin/abuse-events",
    "/api/analytics/admin/kpis",
    "/api/admin/domains",
    "/api/admin/trends",
    "/api/admin/distributions",
    "/api/admin/user-domains",
    "/api/analytics/admin/bias-transparency",
]

for route in routes:
    resp = requests.get(f"{BASE}{route}", headers=h, timeout=30)
    tag = "PASS" if resp.status_code == 200 else "FAIL"
    print(f"  [{tag}] {route} => {resp.status_code}")

# Novelty analyze
resp = requests.post(
    f"{BASE}/api/novelty/analyze",
    headers=h,
    json={"description": "AI drone swarm for pest detection", "domain": "AI & Machine Learning"},
    timeout=180,
)
tag = "PASS" if resp.status_code == 200 else "FAIL"
print(f"  [{tag}] /api/novelty/analyze => {resp.status_code}")
