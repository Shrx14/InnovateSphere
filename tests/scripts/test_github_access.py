"""Test GitHub connectivity and search API access.
Usage: python scripts/test_github_access.py
"""
import os
import sys
import json

try:
    import requests
except Exception:
    print("Please install requests: pip install requests")
    sys.exit(2)

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
BASE = 'https://api.github.com/search/repositories'

def test_search(q='machine learning', per_page=5):
    headers = {'User-Agent': 'InnovateSphere-Test/1.0'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'

    params = {'q': q, 'per_page': per_page}

    try:
        r = requests.get(BASE, headers=headers, params=params, timeout=15)
    except Exception as e:
        print('Request error:', e)
        return None

    print('Status:', r.status_code)
    try:
        data = r.json()
        print('Keys in response:', list(data.keys()))
        items = data.get('items', [])
        print('Items returned:', len(items))
        for i, it in enumerate(items[:3]):
            print(f"[{i}] {it.get('full_name')} - stars={it.get('stargazers_count')}")
        if 'message' in data:
            print('Message:', data['message'])
        return data
    except Exception as e:
        print('Failed to parse JSON:', e)
        print('Body:', r.text[:1000])
        return None

if __name__ == '__main__':
    print('GITHUB_TOKEN set:', bool(GITHUB_TOKEN))
    test_search()
