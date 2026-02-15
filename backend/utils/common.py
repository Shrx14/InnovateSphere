"""
Common utility functions used across the backend.
"""
import logging
from functools import wraps
from sqlalchemy.exc import OperationalError, DisconnectionError

logger = logging.getLogger(__name__)


def db_retry(max_attempts=2):
    """Decorator that retries a Flask view on stale DB connections (Neon serverless)."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from backend.core.db import db
            for attempt in range(max_attempts):
                try:
                    return f(*args, **kwargs)
                except (OperationalError, DisconnectionError) as exc:
                    db.session.rollback()
                    if attempt < max_attempts - 1:
                        logger.warning("DB connection error in %s (attempt %d), retrying: %s", f.__name__, attempt + 1, exc)
                        continue
                    logger.error("DB connection error in %s after %d attempts: %s", f.__name__, max_attempts, exc)
                    raise
            return f(*args, **kwargs)
        return wrapper
    return decorator


def truncate_source_for_prompt(source, max_title=100, max_summary=200):
    """
    Truncate a source dict to a concise string for LLM prompt injection.
    Keeps total per-source token count predictable (~50-75 tokens).

    Args:
        source: Dict with 'title' and optionally 'summary'/'description'
        max_title: Max characters for title
        max_summary: Max characters for summary

    Returns:
        String: "Title: summary..."
    """
    title = str(source.get("title") or source.get("name") or "Untitled")[:max_title]
    summary = str(
        source.get("summary")
        or source.get("description")
        or source.get("metadata", {}).get("abstract", "")
        or ""
    )[:max_summary]
    if summary:
        return f"{title}: {summary}"
    return title


def truncate_novelty_gaps(gaps, max_items=3, max_words=50):
    """
    Truncate a list of novelty gap dicts/strings to a compact representation.

    Args:
        gaps: List of gap dicts (with 'gap' key) or plain strings
        max_items: Maximum number of gaps to include
        max_words: Maximum words per gap description

    Returns:
        List of truncated gap strings
    """
    if not gaps:
        return []
    result = []
    for item in gaps[:max_items]:
        if isinstance(item, dict):
            text = item.get("gap") or item.get("description") or str(item)
        else:
            text = str(item)
        words = text.split()[:max_words]
        result.append(" ".join(words))
    return result


def map_domain_to_external_category(domain):
    """
    Map internal domain names to external API category keywords.
    Returns a list of relevant keywords for the domain that can be used
    in GitHub/Arxiv API searches.
    
    Args:
        domain: Internal domain name (matches the 10 primary domains)
        
    Returns:
        String of space-separated keywords for API queries.
    """
    # Domain-specific keyword mappings for better external API search results
    domain_keywords = {
        'AI & Machine Learning': ['ai', 'machine-learning', 'neural-network', 'nlp', 'deep-learning', 'llm'],
        'Web & Mobile Development': ['web', 'frontend', 'backend', 'react', 'mobile', 'pwa'],
        'Data Science & Analytics': ['data', 'analytics', 'data-science', 'visualization', 'pandas'],
        'Cybersecurity & Privacy': ['security', 'privacy', 'encryption', 'cybersecurity', 'oauth'],
        'Cloud & DevOps': ['cloud', 'devops', 'docker', 'kubernetes', 'aws', 'azure'],
        'Blockchain & Web3': ['blockchain', 'cryptocurrency', 'smart-contract', 'ethereum', 'defi'],
        'IoT & Hardware': ['iot', 'hardware', 'sensor', 'embedded', 'robotics', 'device'],
        'Healthcare & Biotech': ['healthcare', 'health', 'medical', 'biotech', 'genomics'],
        'Education & E-Learning': ['education', 'learning', 'elearning', 'course', 'training'],
        'Business & Productivity Tools': ['business', 'crm', 'saas', 'productivity', 'automation'],
        
        # Legacy mappings for backward compatibility
        'accessibility': ['accessibility', 'a11y'],
        'cognitive_accessibility': ['accessibility', 'cognitive'],
        'web_accessibility': ['accessibility'],
        'security': ['security'],
        'privacy': ['privacy'],
        'education': ['education', 'learning'],
        'healthcare': ['healthcare', 'health'],
        'ecommerce': ['ecommerce', 'shopping'],
        'ai': ['ai', 'machine-learning'],
        'web_development': ['web', 'development'],
        'mobile': ['mobile', 'app'],
        'devops': ['devops', 'deployment'],
        'data': ['data', 'analytics'],
    }
    
    # If domain has a custom mapping, return it
    if domain in domain_keywords:
        keywords = domain_keywords[domain]
        # Return as string to maintain backward compatibility
        return ' '.join(keywords)
    
    # Default: return domain as-is if no mapping exists
    return domain
