import urllib.request
import urllib.parse
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.retrieval.github_client import _generate_query_variations, _extract_key_terms, search_github
from backend.utils import map_domain_to_external_category


def test_key_term_extraction():
    """Test the key term extraction logic"""
    print('\n' + '=' * 80)
    print('Testing key term extraction')
    print('=' * 80)
    
    test_queries = [
        'Browser extension for assisting Cognitive disabled people',
        'Machine learning for data analysis',
        'Web accessibility checker tool',
    ]
    
    for query in test_queries:
        terms = _extract_key_terms(query, max_terms=4)
        print(f'\nQuery: "{query}"')
        print(f'Extracted key terms: {terms}')


def test_query_variations():
    """Test query variation generation"""
    print('\n' + '=' * 80)
    print('Testing query variation generation')
    print('=' * 80)
    
    test_cases = [
        ('Browser extension for assisting Cognitive disabled people', 'cognitive_accessibility'),
        ('Machine learning framework', 'ai'),
        ('Authentication library', 'security'),
    ]
    
    for query, domain in test_cases:
        print(f'\nQuery: "{query}"')
        print(f'Domain: "{domain}"')
        print(f'Domain keywords: "{map_domain_to_external_category(domain)}"')
        
        variations = _generate_query_variations(query, domain)
        print(f'Generated variations ({len(variations)} total):')
        for i, (var_query, var_desc) in enumerate(variations, 1):
            print(f'  {i}. [{var_desc}] "{var_query}"')


def test_github_search_api(query):
    """Test GitHub search with a given query"""
    params = {
        'q': query,
        'sort': 'stars',
        'order': 'desc',
        'per_page': '20'
    }
    
    base_url = 'https://api.github.com/search/repositories'
    query_string = urllib.parse.urlencode(params)
    url = f'{base_url}?{query_string}'
    
    print(f'\n  Query: {query}')
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'InnovateSphere/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            results = data.get('items', [])
            print(f'  Results count: {len(results)}')
            for item in results[:3]:
                desc = item.get('description', '[no description]')[:50]
                print(f'    - {item.get("full_name")}: {desc}')
            return len(results)
    except Exception as e:
        print(f'  Error: {e}')
        return 0


def test_integrated_search():
    """Test the integrated search_github function"""
    print('\n' + '=' * 80)
    print('Testing integrated search_github() function')
    print('=' * 80)
    
    test_cases = [
        ('Browser extension for assisting Cognitive disabled people', 'cognitive_accessibility'),
        ('Accessible web application framework', 'web_accessibility'),
    ]
    
    for query, domain in test_cases:
        print(f'\n\nQuery: "{query}"')
        print(f'Domain: "{domain}"')
        print('-' * 60)
        
        # Test variations manually to show what's being tried
        variations = _generate_query_variations(query, domain)
        for i, (var_query, var_desc) in enumerate(variations, 1):
            print(f'\nVariation {i} [{var_desc}]:')
            count = test_github_search_api(var_query)
            if count > 0:
                print(f'  [SUCCESS] Found {count} results - would stop here')
                break
        else:
            print('\n  [NO RESULTS] All variations exhausted, no results found')
        
        # Now test with the actual search_github function
        print('\nUsing search_github() function:')
        results = search_github(query, domain, max_results=5)
        print(f'  Results returned: {len(results)}')
        for result in results[:3]:
            print(f'    - {result["title"]}: {result["summary"][:50]}')


# Run tests
if __name__ == '__main__':
    print('\n' + '=' * 80)
    print('GitHub Client Testing Suite')
    print('=' * 80)
    
    test_key_term_extraction()
    test_query_variations()
    test_integrated_search()
