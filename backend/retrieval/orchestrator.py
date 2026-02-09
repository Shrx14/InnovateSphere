import datetime
import logging
from backend.retrieval.arxiv_client import search_arxiv
from backend.retrieval.github_client import search_github
from backend.retrieval.source_reputation import get_source_reputation

logger = logging.getLogger(__name__)


def _summarize_query_with_llm(original_query: str, max_chars: int = 120) -> str:
    """Attempt to produce a concise query using the LLM.

    Returns the summarized string on success or the original query on failure.
    This is called only as a fallback when initial retrieval returns no useful
    GitHub results or returns errors.
    """
    if not original_query or len(original_query) <= max_chars:
        return original_query

    try:
        # Import lazily to avoid LLM client setup cost unless needed
        from backend.ai.llm_client import generate_json

        prompt = (
            "You will receive a user's search query. Produce a concise, focused "
            "search phrase suitable for GitHub repository search (no qualifiers). "
            "Output ONLY valid JSON with a single key 'summary'. The summary should "
            f"be {max_chars} characters or less and preserve the main intent.\n\n"
            f"Query: {original_query}\n"
        )

        resp = generate_json(prompt, max_tokens=200, temperature=0.0)
        if isinstance(resp, dict):
            summary = resp.get("summary") or resp.get("query") or resp.get("q")
            if summary and isinstance(summary, str):
                s = summary.strip()
                return s[:max_chars]
    except Exception as e:
        logger.info("LLM summarization failed or unavailable: %s", e)

    # Fallback to truncated original
    return original_query[:max_chars]

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
    # Ensure we pass fetch_limit explicitly so the GitHub client knows how many
    # raw results to request per-variation. Also ask for up to `limit` final
    # candidates from GitHub so the orchestrator can merge and round-robin.
    github_results = search_github(query, domain, fetch_limit=max_per_source, final_top_n=limit)

    # If GitHub returned no results (or only returned due to errors), try a
    # short LLM-generated query and retry once. This avoids calling LLM for
    # every request while improving recall when initial search fails.
    if not github_results:
        logger.info("[Retrieval] GitHub returned no results; attempting LLM summarization and retry")
        short_q = _summarize_query_with_llm(query, max_chars=120)
        if short_q and short_q != query:
            github_results = search_github(short_q, domain, max_per_source)
    
    # If both sources returned no results, retry arXiv with simplified query
    # (in case it was timing out or had transient issues)
    if not arxiv_results and len(github_results) == 0:
        logger.info("[Retrieval] Both sources empty; retrying arXiv with simplified query")
        short_q = _summarize_query_with_llm(query, max_chars=100)
        if short_q and short_q != query:
            arxiv_results = search_arxiv(short_q, domain, max_per_source)

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

    reputation = get_source_reputation()

    for src in unique_sources:
        rep = reputation.get(src.get("url"), {})
        src["admin_rejected_count"] = rep.get("rejected", 0)
        src["admin_validated_count"] = rep.get("validated", 0)

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
    # Ensure we return a diverse set of source types when possible by
    # selecting in a round-robin manner across available source types.
    if ranked_sources:
        available_types = list(dict.fromkeys([s.get('source_type') for s in ranked_sources]))
        if len(available_types) > 1:
            final_sources = []
            # Round-robin pick one per type until we reach limit
            while len(final_sources) < limit:
                added = False
                for t in available_types:
                    for s in ranked_sources:
                        if s.get('source_type') == t and s not in final_sources:
                            final_sources.append(s)
                            added = True
                            break
                    if len(final_sources) >= limit:
                        break
                if not added:
                    # no more unique items to add
                    break
            final_sources = final_sources[:limit]
        else:
            final_sources = ranked_sources[:limit]
    else:
        final_sources = []

    # Tag as tier_1 before semantic filter
    for src in final_sources:
        src["retrieval_tier"] = "tier_1"

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

    for src in final_sources:
        src["retrieval_tier"] = "tier_2"

    # Add confidence scores
    for src in final_sources:
        confidence = (
            0.6 * src.get("similarity_score", 0) +
            0.2 * src.get("admin_validated_count", 0) -
            0.2 * src.get("admin_rejected_count", 0)
        )
        src["confidence"] = max(0, min(1, confidence))  # Clamp to [0,1]

    logging.info(
        "Retrieval result | total_sources=%d | source_types=%s",
        len(final_sources),
        list(set(s.get("source_type") for s in final_sources))
    )

    return {
        "sources": final_sources,
        "retrieved_at": datetime.datetime.utcnow().isoformat() + 'Z'
    }
