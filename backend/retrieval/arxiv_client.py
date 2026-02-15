import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import logging
import datetime
import time
from backend.utils import map_domain_to_external_category

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
    'individuals', 'people', 'users', 'solution', 'system', 'platform',
    'application', 'app', 'using', 'based', 'approach', 'method'
}


def _extract_academic_keywords_with_llm(description: str, domain: str, max_keywords: int = 5) -> dict:
    """
    Extract academic-specific keywords using LLM for arXiv search.
    Returns both compound academic terms (high-specificity) and simple terms.
    
    Args:
        description: User's project description
        domain: Domain/category (e.g., "Software", "Business")
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        Dictionary with 'compound_terms' (2-3 academic concepts) and 'simple_terms' (3 nouns)
    """
    try:
        from backend.ai.llm_client import generate_json
        
        prompt = f"""You are an academic researcher extracting DISCOVERABLE search keywords from project descriptions for arXiv paper search.

Given this project description, extract a MIX of keywords that researchers would ACTUALLY SEARCH FOR on arXiv.
Focus on academic/technical terminology suitable for finding research papers.

Domain: {domain}
Description: {description}

Rules:
- Return 2-3 COMPOUND ACADEMIC TERMS (2-4 words, specific research concepts):
  ✓ Good: "predictive maintenance", "IoT sensor networks", "facility management systems"
  ✓ Good: "resume parsing algorithms", "natural language processing", "interview simulation"
  ✓ Good: "spatial layout optimization", "resource allocation", "real-time scheduling"
  ✗ Bad: "platform", "system", "solution", "application"
  
- Return 3 SIMPLE TECHNICAL TERMS (1-2 words, core technical concepts):
  ✓ Good: "maintenance", "sensors", "NLP", "classification", "optimization", "scheduling", "allocation"
  ✗ Bad: "help", "develop", "create", "build"

- Compound terms help with SPECIFIC ACADEMIC MATCHES (high precision)
- Simple terms help with BROAD COVERAGE (high recall)
- Avoid generic verbs and business terms
- Prioritize the core INNOVATION/TECHNICAL DOMAIN of this idea
- Include domain-specific concepts: if about markets/events/booths, include terms like "marketplace", "event scheduling", "spatial optimization"
- Think: what would researchers title their papers about this topic?

Return valid JSON with this exact format:
{{
    "compound_terms": ["term1", "term2", "term3"],
    "simple_terms": ["term1", "term2", "term3"],
    "search_strategy": "Brief explanation of why these terms enable finding relevant research papers"
}}"""
        
        response = generate_json(prompt, max_tokens=400, temperature=0.1)
        if isinstance(response, dict):
            compound_terms = response.get("compound_terms", [])
            simple_terms = response.get("simple_terms", [])
            
            # Validate we got usable results
            if isinstance(compound_terms, list) and isinstance(simple_terms, list):
                if compound_terms or simple_terms:
                    result = {
                        "compound_terms": compound_terms[:3],  # Max 3 compound terms
                        "simple_terms": simple_terms[:3],  # Max 3 simple terms
                        "all_terms": compound_terms[:3] + simple_terms[:3]
                    }
                    logger.info("[arXiv] LLM extracted academic keywords: compound=%s, simple=%s", 
                               result["compound_terms"], result["simple_terms"])
                    return result
        
        # If response format is unexpected, try legacy format
        if isinstance(response, dict) and "keywords" in response:
            keywords = response.get("keywords", [])
            if isinstance(keywords, list) and keywords:
                # Split into simple (1-2 words) and compound (3+ words)
                simple = [k for k in keywords if len(k.split()) <= 2][:3]
                compound = [k for k in keywords if len(k.split()) > 2][:3]
                result = {
                    "compound_terms": compound,
                    "simple_terms": simple,
                    "all_terms": keywords[:max_keywords]
                }
                logger.info("[arXiv] LLM extracted academic keywords (legacy format): %s", result["all_terms"])
                return result
                
    except Exception as e:
        logger.debug("[arXiv] LLM keyword extraction failed: %s - falling back to heuristic", str(e))
    
    # Fallback to heuristic extraction if LLM fails
    fallback_terms = _extract_key_terms_heuristic(description, max_terms=max_keywords)
    return {
        "compound_terms": fallback_terms[:2],
        "simple_terms": fallback_terms[2:5],
        "all_terms": fallback_terms
    }


def _extract_key_terms_heuristic(query, max_terms=5):
    """
    Extract key terms from a query by filtering stop words and scoring by position and length.
    Fallback heuristic when LLM-based extraction is unavailable.
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
        
        # Position bonus: earlier words score higher
        position_bonus = 1.0 / (1 + 0.5 * i)
        
        # Length bonus: longer words are more specific/technical
        length_bonus = min(len(cleaned) / 15.0, 1.0)
        
        # Combined score
        score = position_bonus * 2.0 + length_bonus * 0.5
        scored_terms.append((cleaned, score))
    
    # Sort by score descending, take top max_terms
    scored_terms.sort(key=lambda x: x[1], reverse=True)
    result = [term for term, _ in scored_terms[:max_terms]]
    
    return result


def _generate_arxiv_query_variations(query, domain, problem_class="general"):
    """
    Generate progressively simpler query variations for arXiv search.
    
    Strategy:
    - Use LLM extraction for substantial queries (>6 words)
    - For short queries, use fast heuristic directly
    - Try compound academic terms first (high specificity)
    - Fall back to simpler terms for broader coverage
    - Apply category restrictions based on problem_class
    
    Variation order:
    1. Compound academic terms (most specific, research-focused)
    2. Simple technical terms (broad coverage)
    3. Compound terms + domain (with context)
    4. Original query (if short enough)
    5. Domain only (fallback)
    
    Args:
        query: Original search query
        domain: Domain/category for the search
        problem_class: Problem classification (optimization, classification, etc.)
        
    Returns:
        List of (search_query, description) tuples ordered by priority
    """
    # Problem-class to arXiv category mapping
    CATEGORY_MAPPING = {
        "optimization": ["cat:cs.DM", "cat:math.OC", "cat:cs.NE"],      # Discrete math, operations research, neural evolution
        "classification": ["cat:cs.LG", "cat:cs.AI", "cat:stat.ML"],    # ML, AI, Statistics
        "simulation": ["cat:cs.GR", "cat:cs.DC", "cat:math.NA"],        # Graphics, distributed, numerical analysis
        "scheduling": ["cat:cs.DM", "cat:math.OC", "cat:cs.DS"],        # Discrete math, OR, data structures
        "anomaly_detection": ["cat:cs.LG", "cat:cs.CR", "cat:stat.AP"], # ML, Crypto, applied stats
        "ranking": ["cat:cs.IR", "cat:cs.LG", "cat:stat.ML"],           # Information retrieval, ML
        "nlp": ["cat:cs.CL", "cat:cs.AI", "cat:stat.ML"],               # Computation/linguistics, AI
        "general": []  # No category restriction
    }
    
    variations = []
    
    # Get domain keywords
    domain_keywords = map_domain_to_external_category(domain)
    if isinstance(domain_keywords, list):
        domain_str = ' '.join(domain_keywords)
    else:
        domain_str = str(domain_keywords) if domain_keywords else ""
    
    # Build category filter for this problem class
    category_filter = ""
    if problem_class != "general" and problem_class in CATEGORY_MAPPING:
        categories = CATEGORY_MAPPING[problem_class]
        if categories:
            category_filter = f"({' OR '.join(categories)})"
            logger.info("[arXiv] applying category restriction for problem_class=%s: %s", 
                       problem_class, category_filter)
    
    # Decide extraction method based on query length and pipeline mode
    from backend.core.config import Config
    word_count = len(query.split()) if query else 0
    
    if Config.HYBRID_MODE or Config.DEMO_MODE:
        # Hybrid/demo mode: always use fast heuristic — no LLM calls in retrieval
        all_terms = _extract_key_terms_heuristic(query, max_terms=6)
        compound_terms = all_terms[:2]
        simple_terms = all_terms[2:6]
        logger.debug("[arXiv] using heuristic extraction (hybrid mode, %d words)", word_count)
    elif word_count > 6:
        # Substantial detailed query: use LLM academic extraction
        keyword_result = _extract_academic_keywords_with_llm(query, domain, max_keywords=6)
        compound_terms = keyword_result.get("compound_terms", [])
        simple_terms = keyword_result.get("simple_terms", [])
        logger.debug("[arXiv] using LLM extraction for long query (%d words)", word_count)
    else:
        # Short query: use fast heuristic
        all_terms = _extract_key_terms_heuristic(query, max_terms=6)
        compound_terms = all_terms[:2]
        simple_terms = all_terms[2:6]
        logger.debug("[arXiv] using heuristic extraction for short query (%d words)", word_count)
    
    # Variation 1: Compound academic terms (highest specificity)
    if compound_terms:
        compound_query = ' AND '.join([f'all:"{term}"' for term in compound_terms[:2]])
        if category_filter:
            compound_query = f"({compound_query}) AND {category_filter}"
        variations.append((compound_query, "compound academic terms"))
    
    # Variation 2: Simple technical terms (broad coverage)
    if simple_terms:
        simple_query = ' AND '.join([f'all:{term}' for term in simple_terms[:3]])
        if category_filter:
            simple_query = f"({simple_query}) AND {category_filter}"
        variations.append((simple_query, "simple technical terms"))
    
    # Variation 3: Compound terms + domain context
    if compound_terms and domain_str:
        compound_domain_query = ' AND '.join([f'all:"{term}"' for term in compound_terms[:2]])
        compound_domain_query += f' AND all:{domain_str}'
        if category_filter:
            compound_domain_query = f"({compound_domain_query}) AND {category_filter}"
        variations.append((compound_domain_query, "compound terms + domain"))
    
    # Variation 4: Simple terms + domain context
    if simple_terms and domain_str:
        simple_domain_query = ' AND '.join([f'all:{term}' for term in simple_terms[:3]])
        simple_domain_query += f' AND all:{domain_str}'
        if category_filter:
            simple_domain_query = f"({simple_domain_query}) AND {category_filter}"
        variations.append((simple_domain_query, "simple terms + domain"))
    
    # Variation 5: Original query (if reasonably short, <150 chars)
    if query and len(query) < 150:
        # Clean and format original query
        clean_query = query.replace('"', '').strip()
        original_query = f'all:{clean_query}'
        if category_filter:
            original_query = f"({original_query}) AND {category_filter}"
        variations.append((original_query, "original query"))
    
    # Variation 6: Domain only (fallback, broadest)
    if domain_str:
        domain_only_query = f'all:{domain_str}'
        if category_filter:
            domain_only_query = f"({domain_only_query}) AND {category_filter}"
        variations.append((domain_only_query, "domain keywords only"))
    
    # If we only have one variation, add original as fallback
    if not variations and query:
        fallback_query = f'all:{query}'
        if category_filter:
            fallback_query = f"({fallback_query}) AND {category_filter}"
        variations.append((fallback_query, "fallback: original query"))
    
    logger.info("[arXiv] generated %d query variations (problem_class=%s): %s", 
                len(variations),
                problem_class,
                [(desc, q[:60] + '...' if len(q) > 60 else q) for q, desc in variations])
    
    return variations


def _execute_arxiv_search(search_query, max_results, timeout_seconds=20):
    """
    Execute a single arXiv search with given query and timeout.
    Returns (results_list, success_boolean, error_message)
    """
    try:
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
        logger.debug("[arXiv] search url=%s", url)

        # Make request with timeout
        try:
            with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
                xml_data = response.read().decode('utf-8')
        except urllib.error.URLError as ue:
            ue_str = str(ue).lower()
            is_timeout = any(timeout_term in ue_str for timeout_term in 
                           ['timed out', 'timeout', 'read operation timed out', 'connection timed out'])
            
            if is_timeout:
                return [], False, f"timeout: {str(ue)}"
            else:
                return [], False, f"urlerror: {str(ue)}"
        except urllib.error.HTTPError as he:
            try:
                body = he.read().decode('utf-8')
            except Exception:
                body = '<unreadable response body>'
            return [], False, f"httperror: status={getattr(he, 'code', None)}, body={body}"
        except Exception as e:
            return [], False, f"request_failed: {str(e)}"

        # Parse XML
        try:
            root = ET.fromstring(xml_data)
        except Exception as e:
            logger.error("[arXiv] failed to parse XML response: %s", str(e))
            logger.debug("[arXiv] xml snippet: %s", (xml_data or '')[:1000])
            return [], False, f"parse_error: {str(e)}"
        
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

        return results, True, None

    except Exception as e:
        logger.error("[arXiv] unexpected error in _execute_arxiv_search: %s", str(e))
        return [], False, f"unexpected_error: {str(e)}"


def search_arxiv(query, domain, max_results=10, problem_class="general"):
    """
    Search arXiv for papers matching the query and domain.
    Uses progressive query simplification with per-variation timeouts.
    Returns a list of normalized source dictionaries.
    
    Strategy:
    - Generate 5-6 query variations (progressively simpler)
    - Each variation gets its own 20-second timeout
    - On timeout, immediately try next simpler variation
    - Return combined results from all successful variations
    - Stop when reaching max_results threshold
    - Restrict categories based on problem_class when applicable
    """
    try:
        # Generate query variations
        variations = _generate_arxiv_query_variations(query, domain, problem_class=problem_class)
        
        if not variations:
            logger.warning("[arXiv] no query variations generated for query=%s domain=%s", query, domain)
            return []
        
        # Track results and effectiveness
        aggregated = {}
        variation_effectiveness = {}
        timeout_variations = []
        success_variations = []
        
        # Per-variation timeout (not cumulative)
        timeout_seconds = 20
        
        for variation_index, (search_query, variation_desc) in enumerate(variations):
            logger.info("[arXiv] trying variation %d: %s | query=%s", 
                       variation_index + 1, variation_desc, search_query[:80])
            
            # Execute search with per-variation timeout
            results, success, error_msg = _execute_arxiv_search(
                search_query, 
                max_results=max_results,
                timeout_seconds=timeout_seconds
            )
            
            if not success:
                if error_msg and "timeout" in error_msg:
                    logger.warning("[arXiv] variation %d '%s' timed out after %ds", 
                                  variation_index + 1, variation_desc, timeout_seconds)
                    timeout_variations.append((variation_index + 1, variation_desc, error_msg))
                    # Continue to next variation immediately (no retry delay)
                    continue
                else:
                    logger.warning("[arXiv] variation %d '%s' failed: %s", 
                                  variation_index + 1, variation_desc, error_msg)
                    continue
            
            # Process successful results
            if results:
                added_count = 0
                for position_in_result, paper in enumerate(results):
                    url = paper.get('url')
                    if not url:
                        continue
                    if url not in aggregated:
                        # Store metadata for tracking
                        metadata = paper.get('metadata', {})
                        metadata['variation_index'] = variation_index
                        metadata['variation_desc'] = variation_desc
                        metadata['position_in_result'] = position_in_result
                        paper['metadata'] = metadata
                        aggregated[url] = paper
                        added_count += 1
                
                # Track effectiveness
                variation_effectiveness[variation_desc] = added_count
                success_variations.append((variation_index + 1, variation_desc, added_count))
                logger.info("[arXiv] variation %d '%s' returned %d items, %d new unique", 
                           variation_index + 1, variation_desc, len(results), added_count)
                
                # NOTE: Removed early-stopping to collect results from ALL variations
                # This allows ranking by specificity rather than just using the first successful query
            else:
                logger.info("[arXiv] variation %d '%s' returned no results, trying next...", 
                           variation_index + 1, variation_desc)
        
        # Log summary of variation effectiveness
        if success_variations:
            best_variation = max(success_variations, key=lambda x: x[2])
            logger.info("[arXiv] most effective variation: #%d '%s' with %d new results", 
                       best_variation[0], best_variation[1], best_variation[2])
        
        if timeout_variations:
            logger.info("[arXiv] %d variations timed out: %s", 
                       len(timeout_variations),
                       [f"#{v[0]} '{v[1]}'" for v in timeout_variations])
        
        # Return aggregated results
        if aggregated:
            # Define specificity scores for each variation type (higher = more specific/relevant)
            specificity_scores = {
                'compound academic terms': 5,
                'simple technical terms': 4,
                'compound terms + domain': 3,
                'simple terms + domain': 2,
                'original query': 1,
                'domain keywords only': 0,
            }
            
            # Determine query_variation_quality based on best variation source
            best_variation_desc = "unknown"
            if success_variations:
                best_variation = max(success_variations, key=lambda x: x[2])
                best_variation_desc = best_variation[1]
            
            # Classify quality: specific-terms, mixed, domain-only, fallback
            if best_variation_desc in ['compound academic terms', 'simple technical terms']:
                query_variation_quality = "specific"
            elif best_variation_desc in ['compound terms + domain', 'simple terms + domain']:
                query_variation_quality = "mixed"
            elif best_variation_desc == 'domain keywords only':
                query_variation_quality = "domain_only"
            else:
                query_variation_quality = "fallback"
            
            # Add specificity score and quality flag to each paper
            for paper in aggregated.values():
                metadata = paper.get('metadata', {})
                variation_desc = metadata.get('variation_desc', 'unknown')
                specificity = specificity_scores.get(variation_desc, 0)
                metadata['specificity_score'] = specificity
                metadata['query_variation_quality'] = query_variation_quality
                metadata['best_variation_desc'] = best_variation_desc
            
            # Sort by:
            # 1. Specificity score (higher first = more specific queries prioritized)
            # 2. Position in original results (earlier positions = more relevant by ArXiv ranking)
            sorted_results = sorted(
                aggregated.values(),
                key=lambda r: (
                    -r.get('metadata', {}).get('specificity_score', 0),  # Negative for descending
                    r.get('metadata', {}).get('position_in_result', 999)
                )
            )
            
            final_results = sorted_results[:max_results]
            
            # Log final summary with specificity breakdown
            from collections import Counter
            specificity_breakdown = Counter([
                r.get('metadata', {}).get('variation_desc', 'unknown')
                for r in final_results
            ])
            variation_summary = list(dict.fromkeys([
                r.get('metadata', {}).get('variation_desc', 'unknown') 
                for r in final_results
            ]))
            logger.info(
                "[arXiv] final results | total_unique=%d | returned=%d | variations_used=%s | specificity_breakdown=%s | query_quality=%s",
                len(aggregated), len(final_results), variation_summary, dict(specificity_breakdown), query_variation_quality
            )
            
            return final_results
        
        # No results from any variation
        logger.warning("[arXiv] all %d query variations exhausted, no results found", len(variations))
        return []

    except Exception as e:
        logger.error("[arXiv] unexpected error in search_arxiv: %s", str(e))
        return []
