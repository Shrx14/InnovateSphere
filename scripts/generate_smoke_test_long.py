"""Longer-timeout smoke test: log in and call /api/ideas/generate with extended timeout
Usage: python scripts/generate_smoke_test_long.py
"""
import sys
import os
import json
import requests

BASE = "http://127.0.0.1:5000"

def login(email, password):
    url = f"{BASE}/api/login"
    resp = requests.post(url, json={"email": email, "password": password}, timeout=30)
    print(f"[login] status={resp.status_code}")
    print(resp.text)
    if resp.status_code != 200:
        return None
    data = resp.json()
    return data.get("access_token")


def generate(token, query, domain_id):
    url = f"{BASE}/api/ideas/generate"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"subject": query, "domain_id": domain_id}
    # Extended timeout for heavy model loads
    resp = requests.post(url, json=payload, headers=headers, timeout=300)
    print(f"[generate] status={resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)
    return resp


def main():
    email = os.getenv("TEST_USER_EMAIL", "test@test.com")
    password = os.getenv("TEST_USER_PASSWORD", "TestUser@123")

    print("Starting long smoke test: login -> generate (timeout=300s)")
    token = login(email, password)
    if not token:
        print("Login failed, cannot proceed to generate")
        sys.exit(2)

    resp = generate(token, "Smart Attendance using facial recognition", 1)
    if resp.status_code == 201:
        print("Generate OK (201)")
        sys.exit(0)
    else:
        print("Generate failed")
        sys.exit(3)

if __name__ == '__main__':
    main()
