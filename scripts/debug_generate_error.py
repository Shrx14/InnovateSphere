#!/usr/bin/env python
"""Debug test to see exact error response from /api/ideas/generate"""
import requests
import json

BASE = 'http://127.0.0.1:5000'

print("=" * 60)
print("DEBUGGING: /api/ideas/generate 422 ERROR")
print("=" * 60)

# Step 1: Login
print("\n1. LOGIN...")
login_resp = requests.post(
    f'{BASE}/api/login',
    json={'email': 'test@test.com', 'password': 'TestUser@123'}
)
print(f"   Status: {login_resp.status_code}")
token = login_resp.json().get('access_token')
print(f"   Token: {token[:30]}..." if token else "   ERROR: No token")

if not token:
    print("LOGIN FAILED - Exiting")
    exit(1)

# Step 2: Test generate endpoint
print("\n2. GENERATE REQUEST...")
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

payload = {
    'query': 'Smart home automation system with AI',
    'domain_id': 1
}

print(f"   Payload: {json.dumps(payload, indent=4)}")
print(f"   Headers: {json.dumps(dict(headers), indent=4)}")

resp = requests.post(
    f'{BASE}/api/ideas/generate',
    json=payload,
    headers=headers,
    timeout=10
)

print(f"\n   Status: {resp.status_code}")
print(f"   Content-Type: {resp.headers.get('Content-Type')}")
print(f"\n   Response Body:")
print(f"   {resp.text}")

# Step 3: Parse error
if resp.status_code == 422:
    try:
        error_data = resp.json()
        print(f"\n   Parsed Error:")
        print(f"   {json.dumps(error_data, indent=4)}")
    except:
        print(f"   (Could not parse JSON)")

print("\n" + "=" * 60)
