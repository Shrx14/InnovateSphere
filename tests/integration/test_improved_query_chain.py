#!/usr/bin/env python3
"""Test improved GitHub query variation chain with selective LLM usage."""

import requests
import json
import time

time.sleep(3)

url = 'http://localhost:5000/api/novelty/analyze'

test_cases = [
    {
        'name': 'Short vague query (3 words) - should use HEURISTIC',
        'description': 'personalized health platform',
        'domain': 'Software'
    },
    {
        'name': 'Long detailed query (8+ words) - should use LLM extraction',
        'description': 'A personalized health platform that combines data-driven fitness guidance with local community support, integrating biometric analysis, adaptive workout plans, and connections to local nutritionists and trainers.',
        'domain': 'Software'
    },
    {
        'name': 'Medium query (5 words) - should use HEURISTIC',
        'description': 'real time chat application platform',
        'domain': 'Software'
    }
]

print("\n" + "="*90)
print("TEST: Improved GitHub Query Variation Chain")
print("="*90 + "\n")

for test in test_cases:
    print(f"\n📋 TEST CASE: {test['name']}")
    print(f"Query: '{test['description']}'")
    print(f"Word count: {len(test['description'].split())}")
    print("-" * 90)
    
    try:
        response = requests.post(url, json={
            'description': test['description'],
            'domain': test['domain']
        }, timeout=120)
        
        result = response.json()
        
        github_sources = [s for s in result.get('sources', []) if s.get('source_type') == 'github']
        
        print(f"\n✅ GitHub sources returned: {len(github_sources)}")
        
        if github_sources:
            print(f"\n   Sample repositories found:")
            for idx, src in enumerate(github_sources[:3], 1):
                print(f"   {idx}. {src.get('title', '')}")
                if src.get('summary'):
                    print(f"      Summary: {(src.get('summary', '')[:80])}...")
                print()
        else:
            print("   ⚠️  No GitHub sources found")
        
        # Check if results are relevant
        query_terms = test['description'].lower().split()
        if github_sources:
            first_repo_title = github_sources[0].get('title', '').lower()
            first_repo_summary = (github_sources[0].get('summary', '') or '').lower()
            
            matches = sum(1 for term in query_terms if len(term) > 4 and (term in first_repo_title or term in first_repo_summary))
            if matches > 0:
                print(f"   ✅ Relevance check: Top repo contains {matches} relevant term(s)")
            else:
                print(f"   ⚠️  Relevance check: Top repo may not be relevant (0 matching terms)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*90)
print("Summary - Expected Behavior:")
print("="*90)
print("""
✅ SHORT QUERY (< 6 words):
   - Uses HEURISTIC extraction (fast, no LLM overhead)
   - Example: 'personalized health platform' (3 words)
    - Query variations: key terms + domain → key terms only → simplified (up to 5) → original → domain

✅ LONG QUERY (> 6 words):
   - Uses LLM SEMANTIC extraction (slower but more accurate)
   - Example: 'A personalized health platform that combines...' (8+ words)
   - Query variations: semantic_keywords + domain → semantic_keywords → simplified → original → domain

✅ IMPROVED FALLBACK CHAIN:
    OLD: key+domain → original query (failed) → domain only (generic)
    NEW: key+domain → key alone → simplified (up to 5 words) → original → domain only
   
    The NEW "simplified key terms (up to 5)" step means:
    - Instead of trying the full original query when 3-term keys fail
    - We try a more focused up-to-5-word version first (e.g., "personalized health adaptive")
    - This avoids falling back to generic domain-only results

✅ BENEFITS:
   1. Better results for user queries by using simplified keywords BEFORE full query
   2. Faster processing for short vague queries (heuristic only)
   3. Smarter LLM usage (only for substantial queries > 6 words)
   4. More intelligent fallback chain prevents irrelevant results
""")
