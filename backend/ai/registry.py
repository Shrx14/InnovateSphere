"""
AI Registry Module (Segment 0.1)

Provides helper functions for AI pipeline versioning.
This module centralizes AI pipeline management to ensure future-proof evolution.
"""

from backend.core.db import db
from backend.core.models import AiPipelineVersion, PromptVersion
from backend.core.config import Config


def get_active_ai_pipeline_version():
    """
    Retrieves the currently active AI pipeline version.

    Returns:
        str: The active version string (e.g., "v2"), or falls back to DEFAULT_AI_PIPELINE_VERSION.

    This function queries the ai_pipeline_versions table for the active version.
    If no active version is found, it falls back to the default configured version.
    """
    try:
        active_version = AiPipelineVersion.query.filter_by(is_active=True).first()
        if active_version:
            return active_version.version
        else:
            # Fallback to default if no active version in DB
            return Config.DEFAULT_AI_PIPELINE_VERSION
    except Exception as e:
        # In case of DB issues, fallback to config
        print(f"Warning: Could not retrieve active AI pipeline version: {e}")
        return Config.DEFAULT_AI_PIPELINE_VERSION


def get_active_prompt_version():
    """
    Retrieves the currently active prompt version.

    Returns:
        dict: The active prompts JSON, or None if no active version is found.

    This function queries the prompt_versions table for the active version.
    If no active version is found, it returns None.
    """
    try:
        active_version = PromptVersion.query.filter_by(is_active=True).first()
        if active_version:
            return active_version.prompts_json
        else:
            return None
    except Exception as e:
        # In case of DB issues, fallback to None
        print(f"Warning: Could not retrieve active prompt version: {e}")
        return None


def get_active_bias_profile():
    """Retrieve the active bias profile record from the database.

    Returns a dict with keys `name`, `version`, and `rules`. Falls back to
    a default empty profile when DB access fails.
    """
    try:
        from backend.core.models import BiasProfile
        bp = BiasProfile.query.filter_by(is_active=True).order_by(BiasProfile.created_at.desc()).first()
        if bp:
            return {"name": bp.name, "version": bp.version, "rules": bp.rules}
    except Exception:
        pass
    return {"name": "default", "version": "default", "rules": {}}
