#!/usr/bin/env python3
"""Test script to verify novelty analysis sources are returned correctly."""

import requests
import json
import time
import sys

# Give server a moment to fully start
time.sleep(3)

# Test the novelty endpoint
url = 'http://localhost:5000/api/novelty/analyze'
payload = {
    'description': 'A personalized health platform that combines data-driven fitness guidance with local community support, integrating biometric analysis, adaptive workout plans, and connections to local nutritionists and trainers.',
    'domain': 'Software'
}

print("Testing Novelty Analysis Endpoint...")
print(f"URL: {url}")
print(f"Domain: {payload['domain']}")
print()

try:
    response = requests.post(url, json=payload, timeout=120)
    result = response.json()
    
    print("=== NOVELTY ANALYSIS RESULT ===")
    print(f"Status Code: {response.status_code}")
    print(f"Novelty Score: {result.get('novelty_score')}")
    print(f"Novelty Level: {result.get('novelty_level')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Domain Intent: {result.get('domain_intent')}")
    print()
    print(f"Sources Found: {len(result.get('sources', []))}")
    
    # Check sources
    if result.get('sources'):
        arxiv_sources = [s for s in result['sources'] if s.get('source_type') == 'arxiv']
        github_sources = [s for s in result['sources'] if s.get('source_type') == 'github']
        
        print(f"  - arXiv papers: {len(arxiv_sources)}")
        print(f"  - GitHub repos: {len(github_sources)}")
        
        if arxiv_sources:
            print("\n=== ARXIV PAPERS (Top 3) ===")
            for idx, src in enumerate(arxiv_sources[:3], 1):
                print(f"{idx}. {src.get('title', 'N/A')[:70]}")
                print(f"   URL: {src.get('url', 'N/A')}")
                print(f"   Summary: {(src.get('summary', '') or '')[:100]}...")
                print()
        
        if github_sources:
            print("=== GITHUB REPOSITORIES (Top 3) ===")
            for idx, src in enumerate(github_sources[:3], 1):
                print(f"{idx}. {src.get('title', 'N/A')}")
                print(f"   URL: {src.get('url', 'N/A')}")
                print(f"   Summary: {(src.get('summary', '') or '')[:100]}...")
                if src.get('confidence'):
                    print(f"   Confidence: {(src.get('confidence') * 100):.0f}%")
                print()
    else:
        print("\n⚠️  No sources returned!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
