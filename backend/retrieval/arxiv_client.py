import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import logging
import datetime
import time
from backend.utils import map_domain_to_external_category

logger = logging.getLogger(__name__)


def search_arxiv(query, domain, max_results=10):

    """
    Search arXiv for papers matching the query and domain.
    Returns a list of normalized source dictionaries.
    """
    try:
        # Build search query: combine query and domain
        # arXiv `cat:` expects specific category codes (e.g., cs.AI). Many internal
        # domain names are human-readable (e.g., "Web Development") and will
        # produce invalid queries. To be robust, append the domain as keywords
        # to the full-text search instead of using `cat:` unless a valid arXiv
        # category code is explicitly provided.
        search_query = f"all:{query}"
        if domain:
            mapped = map_domain_to_external_category(domain)
            # If mapped looks like an arXiv category (contains a dot), use cat:
            if isinstance(mapped, str) and "." in mapped:
                search_query += f" AND cat:{mapped}"
            else:
                # append domain as free-text terms
                search_query += f" AND all:{mapped}"

        # arXiv API parameters
        params = {
            'search_query': search_query,
            'max_results': str(max_results),
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }

        # Build URL
        base_url = 'https://export.arxiv.org/api/query'
        query_string = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_string}"

        # Log request URL
        logger.info("[arXiv] search url=%s", url)

        # Retry logic for arXiv (common to timeout on slow queries)
        max_retries = 2
        timeout_seconds = 20  # Increased from 10s
        xml_data = None
        
        for attempt in range(max_retries):
            try:
                logger.info("[arXiv] attempt %d/%d", attempt + 1, max_retries)
                with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
                    xml_data = response.read().decode('utf-8')
                logger.info("[arXiv] request successful on attempt %d", attempt + 1)
                break  # Success, exit retry loop
            except urllib.error.URLError as ue:
                ue_str = str(ue).lower()
                logger.debug("[arXiv] URLError exception string: %s", ue_str)
                # Check for timeout errors - various possible messages
                is_timeout = any(timeout_term in ue_str for timeout_term in ['timed out', 'timeout', 'read operation timed out', 'connection timed out'])
                
                if is_timeout and attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s
                    logger.warning(f"[arXiv] timeout detected on attempt {attempt + 1}, retrying in {wait_time}s... | error: {str(ue)}")
                    time.sleep(wait_time)
                    continue
                elif is_timeout:
                    logger.error("[arXiv] timeout on final attempt: %s", str(ue))
                    return []
                else:
                    logger.error("[arXiv] URLError (non-timeout): %s", str(ue))
                    return []
            except urllib.error.HTTPError as he:
                try:
                    body = he.read().decode('utf-8')
                except Exception:
                    body = '<unreadable response body>'
                logger.error("[arXiv] HTTPError status=%s body=%s", getattr(he, 'code', None), body)
                return []
            except Exception as e:
                logger.error("[arXiv] request failed: %s", str(e))
                return []
        
        if xml_data is None:
            logger.error("[arXiv] failed to retrieve data after %d retries", max_retries)
            return []

        # Parse XML
        try:
            root = ET.fromstring(xml_data)
        except Exception as e:
            logger.error("[arXiv] failed to parse XML response: %s", str(e))
            logger.debug("[arXiv] xml snippet: %s", (xml_data or '')[:1000])
            return []
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}

        results = []
        for entry in root.findall('atom:entry', namespace):
            title_elem = entry.find('atom:title', namespace)
            summary_elem = entry.find('atom:summary', namespace)
            id_elem = entry.find('atom:id', namespace)
            published_elem = entry.find('atom:published', namespace)

            if title_elem is not None and id_elem is not None:
                title = title_elem.text.strip() if title_elem.text else ""
                summary = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""
                url = id_elem.text.strip() if id_elem.text else ""

                # Extract published date
                published_date = None
                if published_elem is not None and published_elem.text:
                    try:
                        # arXiv dates are in ISO format like 2023-01-01T00:00:00Z
                        dt = datetime.datetime.fromisoformat(published_elem.text.replace('Z', '+00:00'))
                        published_date = dt.date().isoformat()
                    except ValueError:
                        pass

                results.append({
                    "source_type": "arxiv",
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "metadata": {
                        "published_date": published_date
                    }
                })

        return results

    except Exception as e:
        logger.error(f"Error searching arXiv: {str(e)}")
        return []
