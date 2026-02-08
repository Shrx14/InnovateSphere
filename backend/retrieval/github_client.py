# backend/retrieval/github_client.py

import urllib.request
import urllib.parse
import urllib.error
import json
import logging
import datetime
from backend.utils import map_domain_to_external_category

logger = logging.getLogger(__name__)


def search_github(query, domain, max_results=5):

    """
    Search GitHub for repositories matching the query and domain.
    Returns a list of normalized source dictionaries.
    """
    try:
        # Build search query: combine query and domain
        # Avoid using `topic:` with arbitrary domain names (may contain spaces)
        # — instead append the domain as keywords to keep the query valid.
        search_query = query or ""
        if domain:
            mapped = map_domain_to_external_category(domain)
            # append domain as plain keywords (safe for GitHub search)
            search_query = f"{search_query} {mapped}".strip()

        # GitHub enforces a max q length (~256). Truncate long queries early
        # to avoid 422 responses. Keep a sane default cap (240 chars).
        MAX_Q_LEN = 240
        if len(search_query) > MAX_Q_LEN:
            logger.info("[GitHub] truncating long search query from %d to %d chars", len(search_query), MAX_Q_LEN)
            search_query = search_query[:MAX_Q_LEN]

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

        # Log the request URL (safe: no token in URL)
        logger.info("[GitHub] search url=%s", url)

        # Make request with timeout and User-Agent to avoid rate limits
        req = urllib.request.Request(url, headers={'User-Agent': 'InnovateSphere/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as he:
            try:
                body = he.read().decode('utf-8')
            except Exception:
                body = '<unreadable response body>'
            logger.error("[GitHub] HTTPError status=%s body=%s", getattr(he, 'code', None), body)
            return []
        except Exception as e:
            logger.error("[GitHub] request failed: %s", str(e))
            return []

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
                "summary": description,
                "metadata": {
                    "stars": stargazers_count,
                    "last_updated": last_updated
                }
            })

        # If no results returned for query+domain, retry with query-only fallback
        if len(results) == 0 and query:
            try:
                fallback_params = {
                    'q': query,
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': str(min(max_results, 100))
                }
                fallback_qs = urllib.parse.urlencode(fallback_params)
                fallback_url = f"{base_url}?{fallback_qs}"
                logger.info("[GitHub] fallback search url=%s", fallback_url)
                fallback_req = urllib.request.Request(fallback_url, headers={'User-Agent': 'InnovateSphere/1.0'})
                try:
                    with urllib.request.urlopen(fallback_req, timeout=10) as resp2:
                        data2 = json.loads(resp2.read().decode('utf-8'))
                except urllib.error.HTTPError as fhe:
                    try:
                        fbody = fhe.read().decode('utf-8')
                    except Exception:
                        fbody = '<unreadable response body>'
                    logger.error("[GitHub] fallback HTTPError status=%s body=%s", getattr(fhe, 'code', None), fbody)
                    data2 = {}
                except Exception as e:
                    logger.error("[GitHub] fallback request failed: %s", str(e))
                    data2 = {}

                results = []
                for item in data2.get('items', []):
                    name = item.get('name', '')
                    full_name = item.get('full_name', '')
                    html_url = item.get('html_url', '')
                    description = item.get('description', '') or ''
                    stargazers_count = item.get('stargazers_count', 0)
                    updated_at = item.get('updated_at', '')

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
                        "summary": description,
                        "metadata": {
                            "stars": stargazers_count,
                            "last_updated": last_updated
                        }
                    })
                logging.info("[GitHub] fallback results returned | count=%d", len(results[:max_results]))
            except Exception:
                # ignore fallback failure and return what we have (possibly empty)
                pass

        logging.info("[GitHub] results returned | count=%d", len(results[:max_results]))
        return results[:max_results]

    except Exception as e:
        logger.error(f"Error searching GitHub: {str(e)}")
        return []
