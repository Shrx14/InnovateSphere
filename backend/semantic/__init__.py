"""
Semantic analysis and embedding utilities.
Provides text embedding, similarity ranking, and semantic filtering.
"""

from .embedder import Embedder, get_embedder
from .cached_embedder import CachedEmbedder
from .ranker import rank_sources

__all__ = [
    # Embedding
    "Embedder",
    "get_embedder",
    "CachedEmbedder",
    # Ranking
    "rank_sources",
]
