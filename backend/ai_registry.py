"""
AI Registry Module (Segment 0.1)

Provides helper functions for AI pipeline versioning.
This module centralizes AI pipeline management to ensure future-proof evolution.
"""

from backend.db import db
from backend.models import AiPipelineVersion
from backend.config import Config


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
