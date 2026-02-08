import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import logging
import datetime
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

        # Make request with timeout
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                xml_data = response.read().decode('utf-8')
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
