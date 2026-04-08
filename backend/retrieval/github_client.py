# backend/retrieval/github_client.py

import urllib.request
import urllib.parse
import urllib.error
import json
import logging
import datetime
from backend.utils import map_domain_to_external_category
from backend.ai.llm_client import generate_json
from backend.retrieval.keyword_extractor import extract_key_terms_tfidf

logger = logging.getLogger(__name__)

def _extract_semantic_keywords_with_llm(description: str, domain: str, max_keywords: int = 5) -> dict:
    """
    Extract domain-specific semantic keywords using LLM with mixed strategy.
    Returns both simple technical terms (1-2 words) and compound domain concepts
    for better GitHub search coverage.
    
    Args:
        description: User's project description
        domain: Domain/category (e.g., "Software", "Business")
        max_keywords: Maximum number of keywords to extract (default 5 for better coverage)
        
    Returns:
        Dictionary with 'simple_terms' (3) and 'compound_terms' (2), or falls back to heuristic
    """
    try:
        prompt = f"""You are a technical researcher extracting DISCOVERABLE search keywords from project descriptions.

Given this project description, extract a MIX of keywords that developers would ACTUALLY SEARCH FOR on GitHub.
Focus on both short technical terms AND specific compound concepts.

Domain: {domain}
Description: {description}

Rules:
- Return 3 CORE TECHNICAL KEYWORDS (1-2 words each):
  ✓ Good: "resume", "nlp", "interview", "learning", "analytics", "marketplace", "booking", "scheduling"
  ✗ Bad: "resume-analysis-platform", "natural-language-processing-system"
  
- Return 2 DOMAIN-SPECIFIC COMPOUND TERMS (2-3 words, hyphenated or spaced):
  ✓ Good: "interview-simulator", "resume-parser", "ml-pipeline", "text-analysis", "event-management", "vendor-system"
  ✗ Bad: "system", "platform", "solution"

- Simple terms help with BROAD COVERAGE (high recall)
- Compound terms help with SPECIFIC MATCHES (high precision)
- Avoid generic verbs (helps, develops, creates, builds)
- Avoid introductory words (many, some, users, people, individuals)
- Prioritize the core INNOVATION/DOMAIN of this idea
- Include domain-specific concepts: if about markets/events/vendors/booths, include "marketplace", "vendor", "booth", "event-management"

Return valid JSON with this exact format:
{{
    "simple_terms": ["term1", "term2", "term3"],
    "compound_terms": ["compound-term1", "compound-term2"],
    "search_strategy": "Brief explanation of why this mix enables finding similar projects"
}}"""
        
        response = generate_json(
            prompt,
            max_tokens=400,
            temperature=0.1,
            task_type="retrieval_keywords",
        )
        if isinstance(response, dict):
            simple_terms = response.get("simple_terms", [])
            compound_terms = response.get("compound_terms", [])
            
            # Validate we got usable results
            if isinstance(simple_terms, list) and isinstance(compound_terms, list):
                if simple_terms or compound_terms:
                    result = {
                        "simple_terms": simple_terms[:3],  # Max 3 simple terms
                        "compound_terms": compound_terms[:2],  # Max 2 compound terms
                        "all_terms": simple_terms[:3] + compound_terms[:2]
                    }
                    logger.info("[GitHub] LLM extracted semantic keywords: simple=%s, compound=%s", 
                               result["simple_terms"], result["compound_terms"])
                    return result
        
        # If response format is unexpected, try legacy format
        if isinstance(response, dict) and "keywords" in response:
            keywords = response.get("keywords", [])
            if isinstance(keywords, list) and keywords:
                # Split into simple (1-2 words) and compound (3+ words or hyphenated)
                simple = [k for k in keywords if len(k.split()) <= 2 and '-' not in k][:3]
                compound = [k for k in keywords if len(k.split()) > 2 or '-' in k][:2]
                result = {
                    "simple_terms": simple,
                    "compound_terms": compound,
                    "all_terms": keywords[:max_keywords]
                }
                logger.info("[GitHub] LLM extracted semantic keywords (legacy format): %s", result["all_terms"])
                return result
                
    except Exception as e:
        logger.debug("[GitHub] LLM keyword extraction failed: %s - falling back to heuristic", str(e))
    
    # Fallback to heuristic extraction if LLM fails
    fallback_terms = extract_key_terms_tfidf(description, max_terms=max_keywords)
    return {
        "simple_terms": fallback_terms[:3],
        "compound_terms": fallback_terms[3:5],
        "all_terms": fallback_terms
    }



def _extract_key_terms(query, max_terms=5):
    """
    Extract key terms from a query using TF-IDF-style scoring.

    The extractor mixes unigrams, bigrams, and trigrams and prioritizes
    technically discriminative terms.
    
    Args:
        query: Original search query string
        max_terms: Maximum number of key terms to extract (default 5 for better coverage)
        
    Returns:
        List of key terms ordered by significance (position and length weighted)
    """
    if not query:
        return []
    
    return extract_key_terms_tfidf(query, max_terms=max_terms)


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
    
    # Decide extraction method based on query length and pipeline mode
    from backend.core.config import Config
    word_count = len(query.split()) if query else 0
    
    if Config.HYBRID_MODE or Config.DEMO_MODE:
        # Hybrid/demo mode: always use fast heuristic — no LLM calls in retrieval
        all_terms = _extract_key_terms(query, max_terms=5)
        simple_terms = all_terms[:3]
        compound_terms = all_terms[3:5]
        logger.debug("[GitHub] using heuristic extraction (hybrid mode, %d words)", word_count)
    elif word_count > 6:
        # Substantial detailed query: use LLM semantic extraction (now extracts mixed keywords)
        keyword_result = _extract_semantic_keywords_with_llm(query, domain, max_keywords=5)
        simple_terms = keyword_result.get("simple_terms", [])
        compound_terms = keyword_result.get("compound_terms", [])
        all_terms = keyword_result.get("all_terms", [])
        logger.debug("[GitHub] using LLM extraction for long query (%d words)", word_count)
    else:
        # Short vague query: use fast heuristic, skip LLM overhead (now extracts 5 terms)
        all_terms = _extract_key_terms(query, max_terms=5)
        simple_terms = all_terms[:3]
        compound_terms = all_terms[3:5]
        logger.debug("[GitHub] using heuristic extraction for short query (%d words)", word_count)

    
    # Variation 1: Simple terms (3) + domain keywords (broad coverage with domain context)
    if simple_terms and domain_str:
        combined_query = ' '.join(simple_terms) + ' ' + domain_str
        variations.append((combined_query.strip(), "simple terms + domain"))
    
    # Variation 2: Simple terms (3) alone (broad technical coverage)
    if simple_terms:
        simple_terms_query = ' '.join(simple_terms)
        variations.append((simple_terms_query.strip(), "simple terms only"))
    
    # Variation 3: Compound terms (2) + domain keywords (specific matches with context)
    if compound_terms and domain_str:
        compound_domain_query = ' '.join(compound_terms) + ' ' + domain_str
        variations.append((compound_domain_query.strip(), "compound terms + domain"))
    
    # Variation 4: All keywords mixed (full coverage)
    if all_terms:
        all_terms_query = ' '.join(all_terms)
        variations.append((all_terms_query.strip(), "all keywords mixed"))
    
    # Variation 5: LLM-summarized original query (for oversized queries, replaces truncation)
    if query and len(query) > 200:
        try:
            # Import here to avoid circular dependency
            from backend.retrieval.orchestrator import _summarize_query_with_llm
            summarized = _summarize_query_with_llm(query, max_chars=120)
            if summarized and summarized != query and len(summarized) < len(query):
                variations.append((summarized.strip(), "LLM-summarized query"))
                logger.info("[GitHub] using LLM summary for oversized query: %s", summarized)
        except Exception as e:
            logger.debug("[GitHub] LLM summarization failed: %s", str(e))
    
    # Variation 6: Original full query (preserves full context but may be too long)
    # Only add if not already handled by LLM summary
    if query:
        variations.append((query.strip(), "original query"))
    
    # Variation 7: Domain keywords alone (fallback, broadest - use as last resort)
    if domain_str:
        variations.append((domain_str.strip(), "domain keywords only"))
    
    # Variation 8: Synonym variations - try replacing top 2 simple terms with technical synonyms
    # IMPORTANT: Only add synonyms if we have multiple key terms to try
    if simple_terms and len(simple_terms) >= 2:
        for term in simple_terms[:2]:  # Try synonyms for top 2 keywords
            if term in TECHNICAL_SYNONYMS:
                for synonym in TECHNICAL_SYNONYMS[term][:1]:  # Try first synonym only
                    # Replace top keyword with synonym
                    variant_terms = [synonym if t == term else t for t in simple_terms]
                    variant_query = ' '.join(variant_terms)
                    if variant_query and variant_query != simple_terms_query:
                        variations.append((variant_query.strip(), f"synonym variation: {term}→{synonym}"))
                        break  # Only try one synonym per keyword

    
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
        A list of normalized source dictionaries, ordered by relevance (variation priority + position first), then stars.

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
        # Track which variation yields the most results
        variation_effectiveness = {}
        
        for variation_index, (search_query, variation_desc) in enumerate(variations):

            # GitHub enforces a max q length (~256). For non-LLM-summarized queries,
            # truncate long queries to avoid 422 responses. Keep a sane default cap (240 chars).
            MAX_Q_LEN = 240
            if len(search_query) > MAX_Q_LEN and "LLM-summarized" not in variation_desc:
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
                for position_in_result, r in enumerate(results):
                    url = r.get('url')
                    if not url:
                        continue
                    if url not in aggregated:
                        # Store metadata for relevance-aware sorting
                        metadata = r.get('metadata', {})
                        metadata['variation_index'] = variation_index
                        metadata['position_in_result'] = position_in_result
                        r['metadata'] = metadata
                        aggregated[url] = r
                        added_count += 1


                # Track effectiveness of this variation
                variation_effectiveness[variation_desc] = added_count
                logger.info("[GitHub] variation '%s' returned %d items, %d new aggregated", variation_desc, len(results), added_count)

                # Stop early if we've collected enough unique candidates
                if len(aggregated) >= final_top_n:
                    break
            else:
                logger.info("[GitHub] no results for variation '%s', trying next...", variation_desc)
        
        # After trying variations, return up to final_top_n aggregated results
        if aggregated:
            # Log which variation was most effective
            if variation_effectiveness:
                best_variation = max(variation_effectiveness, key=variation_effectiveness.get)
                logger.info("[GitHub] most effective variation: '%s' with %d new results", 
                           best_variation, variation_effectiveness[best_variation])
            
            # Sort results: Use variation priority + position as primary (relevance), stars as tiebreaker
            # Earlier variations = more relevant, earlier position = more relevant
            # Stars only used to break ties when relevance is equal
            # This ensures 0-star but highly-relevant repos aren't buried
            sorted_results = sorted(
                aggregated.values(),
                key=lambda r: (
                    r.get('metadata', {}).get('variation_index', 999),  # Lower index = earlier variation = more relevant
                    r.get('metadata', {}).get('position_in_result', 999),  # Lower position = more relevant within variation
                    -r.get('metadata', {}).get('stars', 0)  # Higher stars = better (negative for descending)
                )
            )
            final_results = sorted_results[:final_top_n]
            
            # Log ranking metadata
            ranking_info = [
                {
                    'title': r['title'][:30],
                    'var_idx': r.get('metadata', {}).get('variation_index', -1),
                    'pos': r.get('metadata', {}).get('position_in_result', -1),
                    'stars': r.get('metadata', {}).get('stars', 0)
                }
                for r in final_results
            ]
            logger.info(
                "[GitHub] aggregated results | total=%d | returned=%d | ranking=(var_idx, pos, stars): %s",
                len(aggregated), len(final_results), ranking_info
            )
            return final_results



        # No results from any variation
        logger.info("[GitHub] all query variations exhausted, no results found")
        return []

    except Exception as e:
        logger.error(f"Error searching GitHub: {str(e)}")
        return []
