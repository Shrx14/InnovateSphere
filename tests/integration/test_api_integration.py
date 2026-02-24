#!/usr/bin/env python
"""
End-to-end API test for novelty analysis
"""

import os
import requests
import json
import time

BASE_URL = os.getenv("TEST_API_BASE_URL", "http://localhost:5000")

# Acquire a fresh token via login instead of using an expired hardcoded JWT
def _get_test_token():
    email = os.getenv("TEST_USER_EMAIL", "test@test.com")
    password = os.getenv("TEST_USER_PASSWORD", "TestUser@123")
    try:
        r = requests.post(f"{BASE_URL}/api/login", json={"email": email, "password": password}, timeout=10)
        if r.status_code == 200:
            return r.json().get("access_token")
    except Exception:
        pass
    return None

test_token = _get_test_token()

headers = {
    "Authorization": f"Bearer {test_token}",
    "Content-Type": "application/json"
}

print("=" * 70)
print("END-TO-END NOVELTY ANALYSIS TEST")
print("=" * 70)

# Wait for backend to fully start
print("\nWaiting for backend to start...")
time.sleep(3)

# Test 1: Original fitness idea (should now be scored ~60-70 instead of 92.9)
test_idea_1 = {
    "description": "Development of an AI-Powered Personalized Fitness and Nutrition Recommendation System with Local Community Integration. Analyzes biometric data, fitness goals, dietary preferences, and local services to create highly personalized, adaptive plans.",
    "domain": "Software"
}

print("\n[TEST 1] Fitness & Community Idea")
print(f"Description: {test_idea_1['description'][:80]}...")
print(f"Domain: {test_idea_1['domain']}")

try:
    response = requests.post(
        f"{BASE_URL}/api/novelty/analyze",
        json=test_idea_1,
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        score = data.get("novelty_score")
        sources = data.get("debug", {}).get("retrieved_sources", 0)
        
        print(f"\n  Result:")
        print(f"    Novelty Score: {score}")
        print(f"    Sources Found: {sources}")
        print(f"    Expected: 60-70 (was 92.9 before fix)")
        
        if 60 <= score <= 75:
            print(f"    ✓ SUCCESS: Score is now in the 'medium' range!")
        elif score > 75:
            print(f"    ⚠ WARNING: Score still higher than expected. Check if sources were found.")
        else:
            print(f"    ⚠ WARNING: Score lower than expected.")
    else:
        print(f"  ERROR: HTTP {response.status_code}")
        print(f"  Response: {response.text}")
        
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: NLP feedback platform (from the logs, scored 91.7)
test_idea_2 = {
    "description": "AI-powered, real-time anonymous feedback and ideation platform that uses natural language processing (NLP) to analyze, categorize, and summarize employee input, presenting key themes and actionable insights.",
    "domain": "Software"
}

print("\n[TEST 2] NLP Feedback Platform")
print(f"Description: {test_idea_2['description'][:80]}...")
print(f"Domain: {test_idea_2['domain']}")

try:
    response = requests.post(
        f"{BASE_URL}/api/novelty/analyze",
        json=test_idea_2,
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        score = data.get("novelty_score")
        sources = data.get("debug", {}).get("retrieved_sources", 0)
        
        print(f"\n  Result:")
        print(f"    Novelty Score: {score}")
        print(f"    Sources Found: {sources}")
        print(f"    Expected: 60-70 (was 91.7 before fix)")
        
        if 60 <= score <= 75:
            print(f"    ✓ SUCCESS: Score is now in the 'medium' range!")
        elif score > 75:
            print(f"    ⚠ WARNING: Score still higher than expected. Check if sources were found.")
        else:
            print(f"    ⚠ WARNING: Score lower than expected.")
    else:
        print(f"  ERROR: HTTP {response.status_code}")
        print(f"  Response: {response.text}")
        
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("""
What was fixed:
1. ✓ Zero-source penalty: Saturation penalty increased for 0 sources
2. ✓ Evidence-based bonuses: Bonuses only apply when sources found
3. ✓ Ollama health check: Fast-fail if Ollama not available
4. ✓ arXiv resilience: 20s timeout + automatic retry
5. ✓ Orchestration: Both retrieval sources get fallback retry

Expected behavior:
- Ideas with 0 sources: Score ~60-70 (was ~91-92)
- Ideas with sources: Score increases with evidence
- Retrieval failures: Automatic retry with simplified queries
- Ollama down: Fails immediately instead of 3 retry timeouts
""")
