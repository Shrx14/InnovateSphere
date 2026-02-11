# backend/retrieval/github_client.py

import urllib.request
import urllib.parse
import urllib.error
import json
import logging
import datetime
from backend.utils import map_domain_to_external_category
from backend.ai.llm_client import generate_json

logger = logging.getLogger(__name__)

# Stop words to filter out when extracting key terms
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'of', 'on', 'or', 'the', 'to',
    'was', 'will', 'with', 'that', 'this', 'have', 'do', 'does',
    'did', 'which', 'who', 'when', 'where', 'why', 'how'
}

# Additional generic verbs and filler words that don't help search
GENERIC_VERBS = {
    'help', 'helps', 'develop', 'develops', 'create', 'creates',
    'build', 'builds', 'make', 'makes', 'provide', 'provides',
    'support', 'manage', 'enable', 'improve', 'enhance', 'many',
    'individuals', 'people', 'users', 'solution', 'system'
}


def _extract_semantic_keywords_with_llm(description: str, domain: str, max_keywords: int = 5) -> list:
    """
    Extract domain-specific semantic keywords using LLM.
    This identifies meaningful technical terms relevant to GitHub search,
    rather than just positional heuristics (e.g., "data-driven" instead of "many").
    
    Args:
        description: User's project description
        domain: Domain/category (e.g., "Software", "Business")
        max_keywords: Maximum number of keywords to extract (default 5 for better coverage)
        
    Returns:
        List of semantic keywords, or falls back to heuristic extraction on error
    """
    try:
        prompt = f"""You are a technical researcher extracting DISCOVERABLE search keywords from project descriptions.

Given this project description, extract 3-5 keywords that developers would ACTUALLY SEARCH FOR on GitHub.
Focus on short, specific technical terms that developers use when exploring similar projects.

Domain: {domain}
Description: {description}

Rules:
- Extract 3-5 keywords (more keywords = better search coverage)
- Keywords should be SHORT and SPECIFIC:
  ✓ Good: "personalized", "fitness", "health-recommendation", "nutrition", "community-health"
  ✗ Bad: "personalized-fitness-system", "community-integrated-health"
- Include single-word technical terms (high recall): "ai", "analytics", "machine-learning"
- Include hyphenated domain concepts (specific): "health-tracking", "adaptive-algorithms"
- Think like a developer searching GitHub: what 2-3 word combos would you type?
- Avoid generic verbs (helps, develops, creates, builds)
- Avoid introductory words (many, some, users, people, individuals)
- Prioritize the core INNOVATION/DOMAIN of this idea

Return valid JSON with this exact format:
{{
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "search_strategy": "Brief explanation of why these keywords enable finding similar projects"
}}"""
        
        response = generate_json(prompt, max_tokens=400, temperature=0.1)
        if isinstance(response, dict) and "keywords" in response:
            keywords = response.get("keywords", [])
            if isinstance(keywords, list) and keywords:
                # Take up to max_keywords, but keep all if LLM returned fewer
                result = keywords[:max_keywords]
                logger.info("[GitHub] LLM extracted semantic keywords: %s", result)
                return result
    except Exception as e:
        logger.debug("[GitHub] LLM keyword extraction failed: %s - falling back to heuristic", str(e))
    
    # Fallback to heuristic extraction if LLM fails
    return _extract_key_terms(description, max_terms=max_keywords)


def _extract_key_terms(query, max_terms=5):
    """
    Extract key terms from a query by filtering stop words and scoring by position and length.
    This is a fallback heuristic when LLM-based extraction is unavailable.
    Returns a list of meaningful terms, prioritizing:
    1. Position (earlier words are more likely to be core concepts)
    2. Length (longer words are more specific/technical)
    
    Args:
        query: Original search query string
        max_terms: Maximum number of key terms to extract (default 5 for better coverage)
        
    Returns:
        List of key terms ordered by significance (position and length weighted)
    """
    if not query:
        return []
    
    # Split into words and convert to lowercase
    words = query.lower().split()
    
    # Score each word by position and length
    scored_terms = []
    for i, w in enumerate(words):
        cleaned = w.strip('.,!?;:')
        # Skip stop words, generic verbs, and very short words
        if (cleaned.lower() in STOP_WORDS 
            or cleaned.lower() in GENERIC_VERBS 
            or len(cleaned) <= 3):
            continue
        
        # Position bonus: earlier words score higher (first word: 1.0, second: 0.67, third: 0.5)
        # This reflects that important concepts usually appear first
        position_bonus = 1.0 / (1 + 0.5 * i)
        
        # Length bonus: longer words are more specific/technical
        # Example: "personalization" (14 chars) scores higher than "fitness" (7 chars)
        length_bonus = min(len(cleaned) / 15.0, 1.0)  # Cap at 1.0 for words longer than 15 chars
        
        # Combined score: position is primary, length is secondary
        score = position_bonus * 2.0 + length_bonus * 0.5
        scored_terms.append((cleaned, score))
    
    # Sort by score descending, take top max_terms
    scored_terms.sort(key=lambda x: x[1], reverse=True)
    result = [term for term, _ in scored_terms[:max_terms]]
    
    return result


# Technical domain synonym mappings for query variation fallback
# When specific keywords don't match well, try synonymous concepts
TECHNICAL_SYNONYMS = {
    "personalized": ["adaptive", "customized", "tailored", "personalization"],
    "distributed": ["decentralized", "scalable", "peer-to-peer"],
    "real-time": ["streaming", "live", "immediate"],
    "machine-learning": ["ai", "neural", "deep-learning"],
    "recommendation": ["recommendations", "recommender", "suggest"],
    "analytics": ["analysis", "metrics", "insights"],
    "health": ["healthcare", "medical", "wellness"],
    "community": ["social", "collaboration", "network"],
}


def _generate_query_variations(query, domain):
    """
    Generate progressively simpler query variations using intelligent fallback chain.
    
    Strategy:
    - Only use expensive LLM extraction for substantial queries (>6 words)
    - For short vague queries, use fast heuristic directly
    - Simplified key terms (up to 5) before original full query to avoid irrelevant results
    - Try technical synonyms for keywords to maximize search coverage
    
    Variation order:
    1. Key terms (5) + domain (most specific, best coverage)
    2. Key terms (5) alone (specific to idea, no domain noise)
    3. Synonym variations (try 1-2 keywords with synonyms)
    4. Simplified key terms (up to 5) - further reduced for better results  
    5. Original full query (full context, but potentially too long)
    6. Domain only (last resort, too generic)
    
    Args:
        query: Original search query
        domain: Domain/category for the search
        
    Returns:
        List of (search_query, description) tuples ordered by priority
    """
    variations = []
    
    # Get domain keywords
    domain_keywords = map_domain_to_external_category(domain)
    if isinstance(domain_keywords, list):
        domain_str = ' '.join(domain_keywords)
    else:
        domain_str = str(domain_keywords) if domain_keywords else ""
    
    # Decide extraction method based on query length
    # Only use expensive LLM for substantial queries
    word_count = len(query.split()) if query else 0
    
    if word_count > 6:
        # Substantial detailed query: use LLM semantic extraction (now extracts 5 keywords)
        key_terms = _extract_semantic_keywords_with_llm(query, domain, max_keywords=5)
        logger.debug("[GitHub] using LLM extraction for long query (%d words)", word_count)
    else:
        # Short vague query: use fast heuristic, skip LLM overhead (now extracts 5 terms)
        key_terms = _extract_key_terms(query, max_terms=5)
        logger.debug("[GitHub] using heuristic extraction for short query (%d words)", word_count)
    
    # Variation 1: Key terms (5) + domain keywords (most specific, best coverage)
    if key_terms and domain_str:
        combined_query = ' '.join(key_terms) + ' ' + domain_str
        variations.append((combined_query.strip(), "key terms + domain"))
    
    # Variation 2: Key terms (5) alone (specific to the idea, without domain noise)
    if key_terms:
        key_terms_query = ' '.join(key_terms)
        variations.append((key_terms_query.strip(), "key terms only"))
    
    # Variation 3: Synonym variations - try replacing top 2 keywords with technical synonyms
    # IMPORTANT: Only add synonyms if we have multiple key terms to try
    if key_terms and len(key_terms) >= 2:
        for term in key_terms[:2]:  # Try synonyms for top 2 keywords
            if term in TECHNICAL_SYNONYMS:
                for synonym in TECHNICAL_SYNONYMS[term][:1]:  # Try first synonym only
                    # Replace top keyword with synonym
                    variant_terms = [synonym if t == term else t for t in key_terms]
                    variant_query = ' '.join(variant_terms)
                    if variant_query and variant_query != key_terms_query:
                        variations.append((variant_query.strip(), f"synonym variation: {term}→{synonym}"))
                        break  # Only try one synonym per keyword
    
    # Variation 4: Simplified key terms (try top-2, top-3, top-4)
    # Try progressively smaller simplified queries before falling back to original.
    # The previous logic could never add a simplified variant when `len(key_terms) <= 5`
    # because it compared the simplified join to the full join and they were identical.
    if key_terms and len(key_terms) >= 2:
        # Try top-N simplified queries (2..min(4, len(key_terms))) to increase hit-rate
        max_try = min(4, len(key_terms))
        seen = set()
        for n in range(2, max_try + 1):
            simplified = ' '.join(key_terms[:n]).strip()
            if not simplified or simplified in seen:
                continue
            seen.add(simplified)
            # Avoid duplicating the exact key_terms query already added as variation 2
            try:
                if key_terms_query and simplified == key_terms_query:
                    continue
            except NameError:
                pass
            variations.append((simplified, f"simplified key terms (top {n})"))
    
    # Variation 5: Original full query (preserves full context but may be too long)
    if query:
        variations.append((query.strip(), "original query"))
    
    # Variation 6: Domain keywords alone (fallback, broadest - use as last resort)
    if domain_str:
        variations.append((domain_str.strip(), "domain keywords only"))
    
    # If we only have one variation, something's wrong - add a generic fallback
    if not variations and query:
        variations.append((query.strip(), "fallback: original query"))
    
    logger.debug("[GitHub] query variations generated: %s", 
                 [(desc, q[:50] + '...' if len(q) > 50 else q) for q, desc in variations])
    
    return variations


def search_github(query, domain, max_results=5, fetch_limit=20, final_top_n=5):
    """
    Search GitHub for repositories matching the query and domain.
    Uses progressive query simplification: tries key terms + domain first,
    then query alone, then domain alone.
    
    Improved ranking strategy:
    - Fetches up to `fetch_limit` results ordered by RELEVANCE (best-match from GitHub API)
    - Locally sorts the fetched results by star count (descending)
    - Returns the top `final_top_n` most-starred results
    
    This ensures we get both relevance AND quality (star count) in the final selection.
    
    Args:
        query: Search query string
        domain: Domain/category for search refinement
        max_results: How many results caller expects (used for backwards-compatibility)
        fetch_limit: How many raw results to fetch from GitHub API (default 20)
        final_top_n: How many results to return after star-sorting (default 5)
    
    Returns:
        A list of normalized source dictionaries, ordered by star count (highest first).
    """
    try:
        # Generate query variations, ordered by expected effectiveness
        variations = _generate_query_variations(query, domain)
        
        if not variations:
            logger.warning("[GitHub] no query variations generated for query=%s domain=%s", query, domain)
            return []
        
        # Try each variation in order and aggregate unique results until we
        # reach the requested quota (`final_top_n`). This differs from the
        # previous behavior which returned immediately on the first
        # non-empty variation. Aggregation improves recall across
        # prioritized variations while still respecting per-call `fetch_limit`.
        aggregated = {}
        for search_query, variation_desc in variations:
            # GitHub enforces a max q length (~256). Truncate long queries early
            # to avoid 422 responses. Keep a sane default cap (240 chars).
            MAX_Q_LEN = 240
            if len(search_query) > MAX_Q_LEN:
                logger.info("[GitHub] truncating query from %d to %d chars (variation: %s)", 
                           len(search_query), MAX_Q_LEN, variation_desc)
                search_query = search_query[:MAX_Q_LEN]
            
            logger.info("[GitHub] trying variation: %s | query=%s", variation_desc, search_query)
            
            # GitHub API parameters
            # NOTE: Omitting 'sort' param means GitHub returns best-match (relevance-ordered)
            # We will sort locally by stars after fetching relevant results
            params = {
                'q': search_query,
                'per_page': str(min(fetch_limit, 100))  # Fetch up to fetch_limit relevant results
            }
            
            # Build URL
            base_url = 'https://api.github.com/search/repositories'
            query_string = urllib.parse.urlencode(params)
            url = f"{base_url}?{query_string}"
            
            # Log the request URL (safe: no token in URL)
            logger.debug("[GitHub] search url=%s", url)
            
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
                logger.warning("[GitHub] HTTPError status=%s body=%s (variation: %s)", 
                             getattr(he, 'code', None), body, variation_desc)
                continue  # Try next variation
            except Exception as e:
                logger.warning("[GitHub] request failed (variation: %s): %s", variation_desc, str(e))
                continue  # Try next variation
            
            # Process results from this variation and add to aggregated map
            results = []
            for item in data.get('items', []):
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

                entry = {
                    "source_type": "github",
                    "title": full_name,
                    "url": html_url,
                    "summary": description,
                    "metadata": {
                        "stars": stargazers_count,
                        "last_updated": last_updated
                    }
                }
                results.append(entry)

            if results:
                # Add unique results to aggregated map keyed by URL
                added_count = 0
                for r in results:
                    url = r.get('url')
                    if not url:
                        continue
                    if url not in aggregated:
                        aggregated[url] = r
                        added_count += 1

                logger.info("[GitHub] variation '%s' returned %d items, %d new aggregated", variation_desc, len(results), added_count)

                # Stop early if we've collected enough unique candidates
                if len(aggregated) >= final_top_n:
                    break
            else:
                logger.info("[GitHub] no results for variation '%s', trying next...", variation_desc)
        
        # After trying variations, return up to final_top_n aggregated results
        if aggregated:
            sorted_results = sorted(
                aggregated.values(),
                key=lambda r: r.get('metadata', {}).get('stars', 0),
                reverse=True
            )
            final_results = sorted_results[:final_top_n]
            logger.info(
                "[GitHub] aggregated results across variations | total_aggregated=%d | returned=%d",
                len(aggregated), len(final_results)
            )
            return final_results

        # No results from any variation
        logger.info("[GitHub] all query variations exhausted, no results found")
        return []

    except Exception as e:
        logger.error(f"Error searching GitHub: {str(e)}")
        return []
