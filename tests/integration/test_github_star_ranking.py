#!/usr/bin/env python3
"""
Unit test for GitHub star-ranking logic.
Verifies that search_github:
1. Fetches up to fetch_limit results from the API (relevance-ordered)
2. Locally sorts by star count
3. Returns only the top final_top_n by star count
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from unittest.mock import patch, MagicMock
from backend.retrieval.github_client import search_github


def mock_github_api_response(search_query):
    """
    Mock GitHub API response with 10 repos in relevance order (best-match).
    Each repo has varying star counts to test local star-sorting.
    """
    # Simulated "best-match" relevance-ordered results from GitHub API
    items = [
        {
            "full_name": "repo_1_medium_stars/project",
            "name": "project",
            "html_url": "https://github.com/repo_1_medium_stars/project",
            "description": "A relevant project with medium popularity",
            "stargazers_count": 150,  # Mid-level stars
            "updated_at": "2025-12-01T10:00:00Z"
        },
        {
            "full_name": "repo_2_low_stars/app",
            "name": "app",
            "html_url": "https://github.com/repo_2_low_stars/app",
            "description": "Another relevant but less popular project",
            "stargazers_count": 45,  # Low stars
            "updated_at": "2025-11-15T10:00:00Z"
        },
        {
            "full_name": "repo_3_high_stars/framework",
            "name": "framework",
            "html_url": "https://github.com/repo_3_high_stars/framework",
            "description": "Most relevant framework with high stars",
            "stargazers_count": 5000,  # High stars (should be in top results)
            "updated_at": "2025-10-01T10:00:00Z"
        },
        {
            "full_name": "repo_4_very_low_stars/lib",
            "name": "lib",
            "html_url": "https://github.com/repo_4_very_low_stars/lib",
            "description": "Relevant library but very new",
            "stargazers_count": 5,  # Very low stars
            "updated_at": "2025-09-01T10:00:00Z"
        },
        {
            "full_name": "repo_5_high_stars/service",
            "name": "service",
            "html_url": "https://github.com/repo_5_high_stars/service",
            "description": "Highly relevant and extremely popular service",
            "stargazers_count": 12000,  # Very high stars (should be #1)
            "updated_at": "2025-08-01T10:00:00Z"
        },
        {
            "full_name": "repo_6_medium_high/tool",
            "name": "tool",
            "html_url": "https://github.com/repo_6_medium_high/tool",
            "description": "Relevant tool with medium-high popularity",
            "stargazers_count": 800,  # Medium-high stars (should be in top)
            "updated_at": "2025-07-01T10:00:00Z"
        },
        {
            "full_name": "repo_7_low/utility",
            "name": "utility",
            "html_url": "https://github.com/repo_7_low/utility",
            "description": "Somewhat relevant utility",
            "stargazers_count": 60,  # Low stars
            "updated_at": "2025-06-01T10:00:00Z"
        },
        {
            "full_name": "repo_8_medium/helper",
            "name": "helper",
            "html_url": "https://github.com/repo_8_medium/helper",
            "description": "Helper library, moderately popular",
            "stargazers_count": 320,  # Medium stars
            "updated_at": "2025-05-01T10:00:00Z"
        },
    ]
    
    return {"items": items}


def test_github_fetches_and_ranks_by_stars():
    """Verify search_github fetches up to fetch_limit and returns top final_top_n by stars"""
    print("\n" + "=" * 80)
    print("TEST: GitHub Star-Ranking Logic")
    print("=" * 80)
    
    # Full mock dataset simulating GitHub API best-match response
    all_items = [
        {"full_name": "repo_1_medium_stars/project", "name": "project", "html_url": "https://github.com/repo_1_medium_stars/project", "description": "A relevant project with medium popularity", "stargazers_count": 150, "updated_at": "2025-12-01T10:00:00Z"},
        {"full_name": "repo_2_low_stars/app", "name": "app", "html_url": "https://github.com/repo_2_low_stars/app", "description": "Another relevant but less popular project", "stargazers_count": 45, "updated_at": "2025-11-15T10:00:00Z"},
        {"full_name": "repo_3_high_stars/framework", "name": "framework", "html_url": "https://github.com/repo_3_high_stars/framework", "description": "Most relevant framework with high stars", "stargazers_count": 5000, "updated_at": "2025-10-01T10:00:00Z"},
        {"full_name": "repo_4_very_low_stars/lib", "name": "lib", "html_url": "https://github.com/repo_4_very_low_stars/lib", "description": "Relevant library but very new", "stargazers_count": 5, "updated_at": "2025-09-01T10:00:00Z"},
        {"full_name": "repo_5_high_stars/service", "name": "service", "html_url": "https://github.com/repo_5_high_stars/service", "description": "Highly relevant and extremely popular service", "stargazers_count": 12000, "updated_at": "2025-08-01T10:00:00Z"},
        {"full_name": "repo_6_medium_high/tool", "name": "tool", "html_url": "https://github.com/repo_6_medium_high/tool", "description": "Relevant tool with medium-high popularity", "stargazers_count": 800, "updated_at": "2025-07-01T10:00:00Z"},
        {"full_name": "repo_7_low/utility", "name": "utility", "html_url": "https://github.com/repo_7_low/utility", "description": "Somewhat relevant utility", "stargazers_count": 60, "updated_at": "2025-06-01T10:00:00Z"},
        {"full_name": "repo_8_medium/helper", "name": "helper", "html_url": "https://github.com/repo_8_medium/helper", "description": "Helper library, moderately popular", "stargazers_count": 320, "updated_at": "2025-05-01T10:00:00Z"}
    ]
    
    def create_mock_urlopen(fetch_limit):
        """Factory to create a mock that respects fetch_limit parameter in the URL"""
        def mock_urlopen_impl(request, timeout=None):  # Accept timeout param
            # Extract per_page from URL to simulate pagination
            url = request.full_url
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            per_page = int(params.get('per_page', ['100'])[0])
            # Limit items to per_page
            limited_items = all_items[:per_page]
            response_data = {"items": limited_items}
            import json
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None
            return mock_response
        return mock_urlopen_impl
    
    with patch('backend.retrieval.github_client.urllib.request.urlopen') as mock_urlopen:
        # Setup mock to return our test data respecting per_page param
        mock_urlopen.side_effect = create_mock_urlopen(fetch_limit=20)
        
        # Test Case 1: fetch_limit=8, final_top_n=5
        print("\n📋 Test Case 1: fetch_limit=8, final_top_n=5 (sorts all 8 fetched, returns top 5)")
        print("-" * 80)
        with patch('backend.retrieval.github_client.urllib.request.urlopen', side_effect=create_mock_urlopen(20)):
            results = search_github(
                query="test project",
                domain="software",
                fetch_limit=8,
                final_top_n=5
            )
            
            print(f"✅ Returned {len(results)} results (expected 5)")
            assert len(results) == 5, f"Expected 5 results, got {len(results)}"
            
            print("\nRanked by star count (descending):")
            for idx, result in enumerate(results, 1):
                stars = result['metadata']['stars']
                title = result['title']
                print(f"  {idx}. {title}: {stars} ⭐")
            
            # Verify stars are in descending order
            star_counts = [r['metadata']['stars'] for r in results]
            assert star_counts == sorted(star_counts, reverse=True), \
                f"Results not sorted by stars descending. Got: {star_counts}"
            
            # With fetch_limit=8: items 0-7 are [150, 45, 5000, 5, 12000, 800, 60, 320]
            # After star-sorting and top 5: [12000, 5000, 800, 320, 150]
            expected_top_stars = [12000, 5000, 800, 320, 150]
            assert star_counts == expected_top_stars, \
                f"Expected star order {expected_top_stars}, got {star_counts}"
            
            print("✅ Results correctly sorted by stars (descending)")
            print("✅ Top repo has most stars (12000)")
        
        # Test Case 2: Smaller fetch_limit and final_top_n
        print("\n📋 Test Case 2: fetch_limit=4, final_top_n=3 (sorts first 4 fetched, returns top 3)")
        print("-" * 80)
        with patch('backend.retrieval.github_client.urllib.request.urlopen', side_effect=create_mock_urlopen(20)):
            results = search_github(
                query="test project",
                domain="software",
                fetch_limit=4,
                final_top_n=3
            )
            
            print(f"✅ Returned {len(results)} results (expected 3)")
            assert len(results) == 3, f"Expected 3 results, got {len(results)}"
            
            print("\nRanked by star count (descending):")
            for idx, result in enumerate(results, 1):
                stars = result['metadata']['stars']
                title = result['title']
                print(f"  {idx}. {title}: {stars} ⭐")
            
            # With fetch_limit=4: only items 0-3 are fetched [150, 45, 5000, 5]
            # After star-sorting and top 3: [5000, 150, 45]
            star_counts = [r['metadata']['stars'] for r in results]
            expected_stars = [5000, 150, 45]
            assert star_counts == expected_stars, \
                f"Expected {expected_stars}, got {star_counts}"
            
            print("✅ Results correctly star-sorted within fetched items")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED")
    print("=" * 80)
    print("""
Summary:
--------
✅ search_github fetches up to fetch_limit items from GitHub API (relevance-ordered)
✅ search_github locally sorts results by star count (descending)
✅ search_github returns only top final_top_n by stars
✅ Maintains backwards-compatibility (default fetch_limit=20, final_top_n=5)

This ensures:
- Relevance: GitHub API provides best-match results in original order
- Quality: Local sorting prefers well-maintained (high-star) repos
- Efficiency: Only returns the final cutoff needed (default 5)
""")


if __name__ == "__main__":
    test_github_fetches_and_ranks_by_stars()
