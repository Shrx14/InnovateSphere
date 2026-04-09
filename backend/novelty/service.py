"""Novelty analysis service - consolidated from services/novelty_service.py"""
import hashlib
import logging
import threading
from functools import lru_cache

_analyzer = None
_analyzer_lock = threading.Lock()
_novelty_cache = {}  # Simple TTL cache: key -> (result, expiry_ts)
_cache_lock = threading.Lock()

logger = logging.getLogger(__name__)


def _get_analyzer():
    """Lazy-load analyzer only when needed (thread-safe)"""
    global _analyzer
    if _analyzer is None:
        with _analyzer_lock:
            if _analyzer is None:
                from backend.novelty.analyzer import NoveltyAnalyzer
                _analyzer = NoveltyAnalyzer()
    return _analyzer


def system_under_load() -> bool:
    """Check if the system is under heavy load.
    Uses job queue depth as a proxy for load."""
    try:
        from backend.generation.job_queue import get_job_queue
        jq = get_job_queue()
        active = jq.count_running_jobs()
        return active >= 5
    except Exception:
        return False


def _cache_key(description: str, domain: str) -> str:
    return hashlib.sha256(f"{domain}:{description}".encode()).hexdigest()


def analyze_novelty(
    description: str,
    domain: str,
    bypass_cache: bool = False,
    preloaded_sources: list | None = None,
    query_text: str | None = None,
) -> dict:
    """Analyze novelty of an idea description within a domain.

    Routes through the domain intent router to detect problem_class,
    then delegates to the appropriate analyzer.

    Results are cached for 10 minutes to avoid redundant computation on
    repeated calls (e.g. admin rescore).

    Args:
        description: The idea description to analyze
        domain: The domain/category for context
        bypass_cache: Force fresh analysis

    Returns:
        dict containing novelty analysis results
    """
    import time

    # Preloaded sources are request-scoped and should not be globally cached.
    use_cache = preloaded_sources is None and query_text is None

    # Check cache (10 min TTL) — thread-safe
    key = _cache_key(description, domain)
    if use_cache and not bypass_cache:
        with _cache_lock:
            if key in _novelty_cache:
                cached_result, expiry = _novelty_cache[key]
                if time.time() < expiry:
                    logger.debug("Novelty cache hit for %s", key[:12])
                    return cached_result

    # Route through domain intent detection
    try:
        from backend.novelty.router import route_engine
        analyzer, used_domain, domain_confidence, problem_class, pc_confidence = route_engine(
            description, override_domain=domain
        )
    except Exception as e:
        logger.warning("Router failed (%s), falling back to direct analyzer", e)
        analyzer = _get_analyzer()
        used_domain = domain
        problem_class = "general"
        domain_confidence = 0.5
        pc_confidence = 0.5

    if system_under_load():
        logger.warning("System under load — running novelty with reduced source limit")

    result = analyzer.analyze(
        description,
        used_domain,
        problem_class=problem_class,
        preloaded_sources=preloaded_sources,
        query_text=query_text,
    )

    # Attach routing metadata for audit
    result["routing"] = {
        "detected_domain": used_domain,
        "domain_confidence": round(domain_confidence, 2),
        "problem_class": problem_class,
        "problem_class_confidence": round(pc_confidence, 2) if pc_confidence else 0.0,
    }

    # Store in cache (10 min TTL) — thread-safe
    if use_cache:
        with _cache_lock:
            _novelty_cache[key] = (result, time.time() + 600)

            # Evict stale entries if cache grows too large
            if len(_novelty_cache) > 200:
                now = time.time()
                stale = [k for k, (_, exp) in _novelty_cache.items() if now >= exp]
                for k in stale:
                    del _novelty_cache[k]

    return result
