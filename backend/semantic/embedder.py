from sentence_transformers import SentenceTransformer
from typing import List

_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder

class Embedder:
    def __init__(self):
        self._embedder = get_embedder()

    def embed_texts(self, texts: List[str]):
        return self._embedder.encode(texts, normalize_embeddings=True)
