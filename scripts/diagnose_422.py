#!/usr/bin/env python3
"""Diagnose the 422 error - see the actual error message"""

import requests
import json
import sys

BASE = "http://127.0.0.1:5000"

def get_token():
    """Get auth token"""
    login_resp = requests.post(
        f"{BASE}/api/login",
        json={"email": "test@test.com", "password": "TestUser@123"}
    )
    if login_resp.status_code != 200:
        print(f"Login failed: {login_resp.status_code}")
        print(login_resp.text)
        return None
    return login_resp.json()["access_token"]

def test_generate(token):
    """Test the generate endpoint with different payloads"""
    
    url = f"{BASE}/api/ideas/generate"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: With "subject" field
    print("\n=== Test 1: Using 'subject' field ===")
    payload = {"subject": "machine learning for healthcare", "domain_id": 1}
    print(f"Payload: {json.dumps(payload)}")
    resp = requests.post(url, json=payload, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    # Test 2: With "query" field
    print("\n=== Test 2: Using 'query' field ===")
    payload = {"query": "machine learning for healthcare", "domain_id": 1}
    print(f"Payload: {json.dumps(payload)}")
    resp = requests.post(url, json=payload, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    # Test 3: With both fields
    print("\n=== Test 3: Using both 'subject' and 'query' fields ===")
    payload = {"subject": "ML healthcare", "query": "machine learning for healthcare", "domain_id": 1}
    print(f"Payload: {json.dumps(payload)}")
    resp = requests.post(url, json=payload, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    # Test 4: Empty subject
    print("\n=== Test 4: Empty 'subject' field ===")
    payload = {"subject": "", "domain_id": 1}
    print(f"Payload: {json.dumps(payload)}")
    resp = requests.post(url, json=payload, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")

if __name__ == "__main__":
    try:
        token = get_token()
        if token:
            print(f"Got token: {token[:20]}...")
            test_generate(token)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
