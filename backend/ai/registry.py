"""
AI Registry Module (Segment 0.1)

Provides helper functions for AI pipeline versioning.
This module centralizes AI pipeline management to ensure future-proof evolution.
"""

import logging
import time
import threading

from backend.core.db import db
from backend.core.models import AiPipelineVersion, PromptVersion
from backend.core.config import Config

logger = logging.getLogger(__name__)

# TTL cache for registry queries (avoids repeated DB hits per generation)
_CACHE_TTL = 60  # seconds
_cache = {}
_cache_lock = threading.Lock()


def _get_cached(key, fetcher):
    """Generic TTL cache wrapper for registry queries."""
    now = time.monotonic()
    with _cache_lock:
        entry = _cache.get(key)
        if entry and now - entry["ts"] < _CACHE_TTL:
            return entry["value"]
    value = fetcher()
    with _cache_lock:
        _cache[key] = {"value": value, "ts": time.monotonic()}
    return value


def get_active_ai_pipeline_version():
    """
    Retrieves the currently active AI pipeline version (cached 60s).

    Returns:
        str: The active version string (e.g., "v2"), or falls back to DEFAULT_AI_PIPELINE_VERSION.
    """
    def _fetch():
        try:
            active_version = AiPipelineVersion.query.filter_by(is_active=True).first()
            if active_version:
                return active_version.version
            return Config.DEFAULT_AI_PIPELINE_VERSION
        except Exception as e:
            logger.warning("Could not retrieve active AI pipeline version: %s", e)
            return Config.DEFAULT_AI_PIPELINE_VERSION

    return _get_cached("pipeline_version", _fetch)


def get_active_prompt_version():
    """
    Retrieves the currently active prompt version (cached 60s).

    Returns:
        dict: The active prompts JSON, or None if no active version is found.
    """
    def _fetch():
        try:
            active_version = PromptVersion.query.filter_by(is_active=True).first()
            if active_version:
                return active_version.prompts_json
            return None
        except Exception as e:
            logger.warning("Could not retrieve active prompt version: %s", e)
            return None

    return _get_cached("prompt_version", _fetch)


def get_active_bias_profile():
    """Retrieve the active bias profile record from the database (cached 60s).

    Returns a dict with keys `name`, `version`, and `rules`. Falls back to
    a default empty profile when DB access fails.
    """
    def _fetch():
        try:
            from backend.core.models import BiasProfile
            bp = BiasProfile.query.filter_by(is_active=True).order_by(BiasProfile.created_at.desc()).first()
            if bp:
                return {"name": bp.name, "version": bp.version, "rules": bp.rules}
        except Exception as e:
            logger.warning("Could not retrieve active bias profile: %s", e)
        return {"name": "default", "version": "default", "rules": {}}

    return _get_cached("bias_profile", _fetch)
