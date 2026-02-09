#!/usr/bin/env python
"""Test different field names to diagnose the 422 error"""
import requests
import json

BASE = 'http://127.0.0.1:5000'

print("=" * 70)
print("TESTING: Different Payload Formats for /api/ideas/generate") 
print("=" * 70)

# Login first
login_resp = requests.post(
    f'{BASE}/api/login',
    json={'email': 'test@test.com', 'password': 'TestUser@123'}
)
token = login_resp.json().get('access_token')
if not token:
    print("Login failed!")
    exit(1)

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Test different payload formats
test_payloads = [
    {
        "name": "Format 1: query + domain_id",
        "payload": {'query': 'AI chatbot for healthcare', 'domain_id': 1}
    },
    {
        "name": "Format 2: subject + domain_id",
        "payload": {'subject': 'AI chatbot for healthcare', 'domain_id': 1}
    },
    {
        "name": "Format 3: subject + domain",
        "payload": {'subject': 'AI chatbot for healthcare', 'domain': 'Artificial Intelligence'}
    },
    {
        "name": "Format 4: description + domain_id",
        "payload": {'description': 'AI chatbot for healthcare', 'domain_id': 1}
    },
    {
        "name": "Format 5: All fields",
        "payload": {
            'query': 'AI chatbot for healthcare',  
            'subject': 'AI chatbot for healthcare',
            'domain_id': 1
        }
    }
]

for test in test_payloads:
    print(f"\n{test['name']}")
    print(f"Payload: {json.dumps(test['payload'])}")
    
    resp = requests.post(
        f'{BASE}/api/ideas/generate',
        json=test['payload'],
        headers=headers,
        timeout=5
    )
    
    print(f"Status: {resp.status_code}")
    try:
        error_data = resp.json()
        print(f"Response: {json.dumps(error_data)}")
    except:
        print(f"Response: {resp.text[:200]}")

print("\n" + "=" * 70)
