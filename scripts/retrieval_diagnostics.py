#!/usr/bin/env python3
"""Diagnostics for GitHub retrieval and idea generation endpoints."""

import argparse
import json
import os
import time
from datetime import datetime

import requests

from backend.retrieval.github_client import _generate_query_variations, _extract_key_terms, search_github
from backend.utils import map_domain_to_external_category


def run_github_diagnostics():
    print("\n" + "=" * 80)
    print("GitHub Retrieval Diagnostics")
    print("=" * 80)

    test_queries = [
        "Browser extension for assisting Cognitive disabled people",
        "Machine learning for data analysis",
        "Web accessibility checker tool",
    ]

    print("\nKey term extraction")
    for query in test_queries:
        terms = _extract_key_terms(query, max_terms=4)
        print(f"- {query}: {terms}")

    print("\nQuery variations")
    test_cases = [
        ("Browser extension for assisting Cognitive disabled people", "cognitive_accessibility"),
        ("Machine learning framework", "ai"),
        ("Authentication library", "security"),
    ]

    for query, domain in test_cases:
        print(f"\nQuery: {query}")
        print(f"Domain: {domain}")
        print(f"Domain keywords: {map_domain_to_external_category(domain)}")
        variations = _generate_query_variations(query, domain)
        for i, (var_query, var_desc) in enumerate(variations, 1):
            print(f"  {i}. [{var_desc}] {var_query}")

    print("\nIntegrated search_github()")
    for query, domain in [
        ("Browser extension for assisting Cognitive disabled people", "cognitive_accessibility"),
        ("Accessible web application framework", "web_accessibility"),
    ]:
        print(f"\nQuery: {query}")
        print(f"Domain: {domain}")
        results = search_github(query, domain, max_results=5)
        print(f"Results: {len(results)}")
        for result in results[:3]:
            print(f"  - {result['title']}: {result.get('summary', '')[:60]}")


def _get_auth_token(base_url: str) -> str | None:
    token = os.getenv("TEST_AUTH_TOKEN")
    if token:
        return token

    email = os.getenv("TEST_USER_EMAIL", "test@test.com")
    password = os.getenv("TEST_USER_PASSWORD", "TestUser@123")
    try:
        resp = requests.post(
            f"{base_url}/api/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception:
        return None
    return None


def run_generation_tests(base_url: str):
    print("\n" + "=" * 80)
    print("Idea Generation Retrieval Tests")
    print("=" * 80)

    token = _get_auth_token(base_url)
    if not token:
        print("No auth token available. Set TEST_AUTH_TOKEN or TEST_USER_EMAIL/TEST_USER_PASSWORD.")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    test_queries = [
        {
            "query": "Development of an AI-Powered Personalized Fitness and Nutrition Recommendation System with Local Community Integration",
            "domain_id": 1,
            "description": "Original failing query - tests keyword extraction improvements",
        },
        {
            "query": "Web application for collaborative project management with real-time updates",
            "domain_id": 2,
            "description": "Web development query - tests lower threshold",
        },
        {
            "query": "Machine learning system for time series forecasting",
            "domain_id": 1,
            "description": "Simpler AI query - tests heuristic extraction",
        },
    ]

    for test_query in test_queries:
        print("\n" + "-" * 80)
        print(f"TEST: {test_query['description']}")
        print(f"Query: {test_query['query'][:60]}...")
        print(f"Domain ID: {test_query['domain_id']}")
        print(f"Time: {datetime.now().isoformat()}")

        payload = {
            "subject": test_query["query"],
            "domain_id": test_query["domain_id"],
        }

        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/api/ideas/generate",
                json=payload,
                headers=headers,
                timeout=90,
            )
            elapsed = time.time() - start_time

            print(f"Response Status: {response.status_code}")
            print(f"Response Time: {elapsed:.2f}s")

            if response.status_code in (200, 201, 202):
                data = response.json()
                if "job_id" in data:
                    print(f"Job ID: {data['job_id']}")
                if "novelty_score" in data:
                    print(f"Novelty Score: {data['novelty_score']}")
            else:
                print(f"Unexpected response: {response.text[:200]}")

        except requests.exceptions.Timeout:
            print("Timeout: Request took too long")
        except requests.exceptions.ConnectionError:
            print("Connection error: Could not reach backend")
        except Exception as exc:
            print(f"Error: {type(exc).__name__}: {exc}")


def main():
    parser = argparse.ArgumentParser(description="Retrieval diagnostics")
    parser.add_argument("--base-url", default=os.getenv("TEST_API_BASE_URL", "http://localhost:5000"))
    parser.add_argument("--github", action="store_true", help="Run GitHub retrieval diagnostics")
    parser.add_argument("--generate", action="store_true", help="Run idea generation retrieval tests")
    args = parser.parse_args()

    run_all = not args.github and not args.generate
    if args.github or run_all:
        run_github_diagnostics()
    if args.generate or run_all:
        run_generation_tests(args.base_url)


if __name__ == "__main__":
    main()
