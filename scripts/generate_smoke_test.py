"""Smoke test: log in and call /api/ideas/generate
Usage: python scripts/generate_smoke_test.py
"""
import sys
import os
import json
import time
import argparse

try:
    import requests
except Exception as e:
    print("requests not installed. Install with: pip install requests")
    raise

BASE = "http://127.0.0.1:5000"

def login(email, password):
    url = f"{BASE}/api/login"
    resp = requests.post(url, json={"email": email, "password": password}, timeout=30)
    print(f"[login] status={resp.status_code}")
    try:
        print(resp.text)
    except:
        pass
    if resp.status_code != 200:
        return None
    data = resp.json()
    return data.get("access_token")


def generate(token, query, domain_id, timeout_seconds):
    url = f"{BASE}/api/ideas/generate"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"subject": query, "domain_id": domain_id}
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout_seconds)
    print(f"[generate] status={resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)
    return resp


def _parse_args():
    parser = argparse.ArgumentParser(description="Smoke test: login -> generate")
    parser.add_argument("--query", default=os.getenv("TEST_GENERATE_QUERY", "Smart Attendance using facial recognition"))
    parser.add_argument("--domain-id", type=int, default=int(os.getenv("TEST_GENERATE_DOMAIN_ID", "1")))
    parser.add_argument("--timeout", type=int, default=int(os.getenv("TEST_GENERATE_TIMEOUT", "60")))
    parser.add_argument("--long", action="store_true", help="Use a 300s timeout for slow model loads")
    return parser.parse_args()


def main():
    args = _parse_args()
    email = os.getenv("TEST_USER_EMAIL", "test@test.com")
    password = os.getenv("TEST_USER_PASSWORD", "TestUser@123")

    timeout_seconds = 300 if args.long else args.timeout

    print("Starting smoke test: login -> generate")
    token = login(email, password)
    if not token:
        print("Login failed, cannot proceed to generate")
        sys.exit(2)

    # Use domain_id 1 (seeded). Adjust if needed.
    resp = generate(token, args.query, args.domain_id, timeout_seconds)
    if resp.status_code == 201:
        print("Generate OK (201)")
        sys.exit(0)
    else:
        print("Generate failed")
        sys.exit(3)

if __name__ == '__main__':
    main()
