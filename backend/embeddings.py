import logging
from sentence_transformers import SentenceTransformer
from backend.config import Config

logger = logging.getLogger(__name__)
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            logger.info("Loading embedding model: %s", Config.EMBEDDING_MODEL)
            _embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        except Exception:
            logger.exception("Failed to load embedding model")
            return None
    return _embedding_model
