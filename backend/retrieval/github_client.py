# backend/retrieval/github_client.py

import urllib.request
import urllib.parse
import json
import logging
import datetime

logger = logging.getLogger(__name__)

def search_github(query, domain, max_results=5):
    """
    Search GitHub for repositories matching the query and domain.
    Returns a list of normalized source dictionaries.
    """
    try:
        # Build search query: combine query and domain
        search_query = query
        if domain:
            search_query += f" topic:{domain}"

        # GitHub API parameters
        params = {
            'q': search_query,
            'sort': 'stars',  # Sort by stars
            'order': 'desc',
            'per_page': str(min(max_results, 100))  # Max 100 per page
        }

        # Build URL
        base_url = 'https://api.github.com/search/repositories'
        query_string = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_string}"

        # Make request with timeout and User-Agent to avoid rate limits
        req = urllib.request.Request(url, headers={'User-Agent': 'InnovateSphere/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        results = []
        for item in data.get('items', []):
            name = item.get('name', '')
            full_name = item.get('full_name', '')
            html_url = item.get('html_url', '')
            description = item.get('description', '') or ''
            stargazers_count = item.get('stargazers_count', 0)
            updated_at = item.get('updated_at', '')

            # Parse last_updated
            last_updated = None
            if updated_at:
                try:
                    dt = datetime.datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    last_updated = dt.date().isoformat()
                except ValueError:
                    pass

            results.append({
                "source_type": "github",
                "title": full_name,
                "url": html_url,
                "description": description,
                "stars": stargazers_count,
                "last_updated": last_updated
            })

        return results[:max_results]

    except Exception as e:
        logger.error(f"Error searching GitHub: {str(e)}")
        return []
