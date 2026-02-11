import hashlib
import time
from typing import Dict

from backend.retrieval.orchestrator import retrieve_sources

_CACHE: Dict[str, tuple] = {}
TTL_SECONDS = 6 * 60 * 60  # 6 hours


def _make_key(**kwargs) -> str:
    """
    Generate cache key from all keyword arguments.
    This ensures that different parameter combinations (e.g., different 'limit' values,
    or different GitHub selection parameters like fetch_limit/final_top_n if added)
    produce different cache entries.
    
    NOTE: GitHub client parameters (fetch_limit, final_top_n) are internal to search_github
    and not directly passed to retrieve_sources. If these are ever configurable at the
    orchestrator level, they should be included in kwargs to ensure proper cache isolation.
    """
    raw = "|".join(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return hashlib.sha256(raw.encode()).hexdigest()


def cached_retrieve_sources(**kwargs) -> dict:
    key = _make_key(**kwargs)
    now = time.time()

    if key in _CACHE:
        ts, data = _CACHE[key]
        if now - ts < TTL_SECONDS:
            return data

    result = retrieve_sources(**kwargs)
    _CACHE[key] = (now, result)
    return result
