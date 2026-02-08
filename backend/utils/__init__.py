"""
Shared utilities for the backend.
"""
from .auth import require_admin, get_current_user_id
from .serializers import serialize_public_idea, serialize_full_idea
from .common import map_domain_to_external_category
from .health_checks import (
    run_startup_checks,
    check_llm,
    check_embeddings,
    check_retrieval,
)

__all__ = [
    'require_admin',
    'get_current_user_id',
    'serialize_public_idea',
    'serialize_full_idea',
    'map_domain_to_external_category',
    'run_startup_checks',
    'check_llm',
    'check_embeddings',
    'check_retrieval',
]
