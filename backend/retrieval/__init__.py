"""
External source retrieval module.
Provides clients for searching and retrieving data from external sources.
"""

from .arxiv_client import search_arxiv
from .github_client import search_github

from .cached_retrieval import cached_retrieve_sources
from .orchestrator import retrieve_sources
from .source_reputation import get_source_reputation

__all__ = [
    # ArXiv
    "search_arxiv",
    # GitHub
    "search_github",
    # Caching
    "cached_retrieve_sources",
    # Orchestration
    "retrieve_sources",
    # Reputation
    "get_source_reputation",
]
