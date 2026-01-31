import datetime
import logging
from backend.retrieval.arxiv_client import search_arxiv
from backend.retrieval.github_client import search_github

def retrieve_sources(
    query,
    domain,
    limit=10,
    semantic_filter=False,
    similarity_threshold=0.6,
    source_types=None,
):
    """
    Orchestrate retrieval from multiple sources.
    Returns structured results with sources and retrieved_at timestamp.
    """
    if source_types is None:
        source_types = ["arxiv", "github"]

    # Cap max_results per source to prevent excessive API calls
    max_per_source = min(limit * 2, 20)  # Reasonable cap

    # Search both sources
    arxiv_results = search_arxiv(query, domain, max_per_source)
    github_results = search_github(query, domain, max_per_source)

    # Merge results
    all_sources = arxiv_results + github_results

    # Filter by source_types if specified
    if source_types:
        all_sources = [s for s in all_sources if s.get('source_type') in source_types]

    # Deduplicate by URL
    seen_urls = set()
    unique_sources = []
    for source in all_sources:
        url = source.get('url')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_sources.append(source)

    # Apply simple ranking
    def sort_key(source):
        if source['source_type'] == 'arxiv':
            # For arXiv, prefer more recent publications
            pub_date = source.get('metadata', {}).get('published_date')
            if pub_date:
                try:
                    return (0, datetime.date.fromisoformat(pub_date))  # Recent first
                except ValueError:
                    pass
            return (0, datetime.date.min)
        elif source['source_type'] == 'github':
            # For GitHub, prefer higher star count
            stars = source.get('metadata', {}).get('stars', 0)
            return (1, stars)  # Higher stars first
        return (2, 0)  # Fallback

    # Sort by ranking (recent/high-stars first)
    ranked_sources = sorted(unique_sources, key=sort_key, reverse=True)

    # Return at most limit results
    final_sources = ranked_sources[:limit]

    # Optional semantic filtering stage
    if semantic_filter:
        try:
            from backend.semantic.filter import filter_by_semantic_similarity
            from backend.semantic.ranker import rank_sources

            filtered = filter_by_semantic_similarity(
                query,
                final_sources,
                similarity_threshold
            )
            final_sources = rank_sources(filtered)

        except Exception:
            pass

    logging.info(
        "Retrieval result | total_sources=%d | source_types=%s",
        len(final_sources),
        list(set(s.get("source_type") for s in final_sources))
    )

    return {
        "sources": final_sources,
        "retrieved_at": datetime.datetime.utcnow().isoformat() + 'Z'
    }
