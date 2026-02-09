#!/usr/bin/env python
"""
Test script to validate improved retrieval and idea generation.
Tests the same query that previously returned 400 due to insufficient sources.
"""
import requests
import json
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:5000"
API_ENDPOINT = f"{BASE_URL}/api/ideas/generate"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3MDY1NTg1OCwianRpIjoiZmJhYWMzZjQtZTVhMi00ODUzLThkZTUtODBjMmMxYjI1ZWUwIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6OCwibmJmIjoxNzcwNjU1ODU4LCJleHAiOjE3NzA2NTY3NTgsInJvbGUiOiJ1c2VyIiwiZW1haWwiOiJ0ZXN0QHRlc3QuY29tIiwicHJlZmVycmVkX2RvbWFpbl9pZCI6bnVsbH0.Ytr7Fh5u0xEfCnz9bMkATQWDiGJUH4n2NHVi24QlJLU"

# Test queries
TEST_QUERIES = [
    {
        "query": "Development of an AI-Powered Personalized Fitness and Nutrition Recommendation System with Local Community Integration",
        "domain_id": 1,  # AI
        "description": "Original failing query - tests keyword extraction improvements"
    },
    {
        "query": "Web application for collaborative project management with real-time updates",
        "domain_id": 2,  # Web Development
        "description": "Web development query - tests lower threshold"
    },
    {
        "query": "Machine learning system for time series forecasting",
        "domain_id": 1,  # AI
        "description": "Simpler AI query - tests heuristic extraction"
    }
]

def test_endpoint(query: str, domain_id: int, description: str):
    """Test the /api/ideas/generate endpoint"""
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"Query: {query[:60]}...")
    print(f"Domain ID: {domain_id}")
    print(f"Time: {datetime.now().isoformat()}")
    print('='*80)
    
    payload = {
        "query": query,
        "domain_id": domain_id
    }
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=90
        )
        elapsed = time.time() - start_time
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Time: {elapsed:.2f}s")
        
        if response.status_code == 201:
            print("✅ SUCCESS: Idea generated (201)")
            data = response.json()
            
            # Print summary of generated idea
            if "final" in data:
                final = data["final"]
                print(f"\nGenerated Idea Summary:")
                print(f"  Title: {final.get('title', 'N/A')[:60]}...")
                print(f"  Problem: {final.get('problem', 'N/A')[:60]}...")
                
            # Print source info
            if "sources" in data:
                sources = data["sources"]
                print(f"\nSources Used: {len(sources)} total")
                for src in sources[:3]:
                    print(f"  - [{src.get('source_type')}] {src.get('title', 'N/A')[:60]}...")
                    
            # Print novelty score
            if "novelty_score" in data:
                print(f"\nNovelty Score: {data['novelty_score']}")
                
        elif response.status_code == 400:
            print("❌ FAILED: 400 Bad Request")
            data = response.json()
            print(f"Error: {data.get('error', 'Unknown error')}")
            
            # Try to extract more details
            if "message" in data:
                print(f"Message: {data['message']}")
        else:
            print(f"⚠️  UNEXPECTED: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Request took too long (>60s)")
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Could not reach backend")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")

def main():
    print("InnovateSphere Retrieval Improvement Testing")
    print("=" * 80)
    print("Testing improved keyword extraction and semantic filtering")
    print()
    
    for test_query in TEST_QUERIES:
        test_endpoint(
            test_query["query"],
            test_query["domain_id"],
            test_query["description"]
        )
    
    print(f"\n{'='*80}")
    print("Testing complete!")
    print(f"Check logs at: {datetime.now().isoformat()}")
    print('='*80)

if __name__ == "__main__":
    main()
