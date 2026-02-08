#!/usr/bin/env python3
"""Detailed diagnostic of the 422 error"""

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
    """Test the generate endpoint"""
    
    url = f"{BASE}/api/ideas/generate"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {"subject": "test query", "domain_id": 1}
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload)}")
    
    resp = requests.post(url, json=payload, headers=headers)
    print(f"\nStatus: {resp.status_code}")
    print(f"Headers: {dict(resp.headers)}")
    print(f"Response Text: {resp.text}")
    
    try:
        print(f"Response JSON: {resp.json()}")
    except:
        print("Could not parse as JSON")

if __name__ == "__main__":
    try:
        token = get_token()
        if token:
            print(f"Got token: {token[:20]}...\n")
            test_generate(token)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
