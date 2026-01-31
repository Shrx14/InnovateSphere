import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import logging
import datetime

logger = logging.getLogger(__name__)

def search_arxiv(query, domain, max_results=10):
    """
    Search arXiv for papers matching the query and domain.
    Returns a list of normalized source dictionaries.
    """
    try:
        # Build search query: combine query and domain
        search_query = f"all:{query}"
        if domain:
            search_query += f" AND cat:{domain}"

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

        # Make request with timeout
        with urllib.request.urlopen(url, timeout=10) as response:
            xml_data = response.read().decode('utf-8')

        # Parse XML
        root = ET.fromstring(xml_data)
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
