import os
from typing import List

from flask import logging
from schedule import logger

# Hard kill switch for legacy ingestion/RAG
ENABLE_LEGACY_AI = False


class Config:
    """
    Centralized configuration for InnovateSphere.
    Designed for:
    - Live retrieval (no ingestion)
    - LLM-first idea generation
    - Evidence-grounded novelty scoring
    """

    # =========================================================
    # Database
    # =========================================================
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    RAG_DATABASE_URL = os.getenv("RAG_DATABASE_URL", "")  # kept for backward compatibility

    # =========================================================
    # Security / Authentication
    # =========================================================
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret")
    JWT_ALGO = os.getenv("JWT_ALGO", "HS256")
    JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", 3600))

    # =========================================================
    # Embeddings (semantic filtering & similarity)
    # =========================================================
    # all-MiniLM-L6-v2 is:
    # - fast
    # - low memory
    # - strong enough for semantic narrowing
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 384))

    # =========================================================
    # LLM Configuration
    # =========================================================
    # Supported: "ollama" | "openai"
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

    # Ollama (local, free, default)
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "phi3:mini")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # OpenAI (optional, paid)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # LLM runtime safety
    LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", 15))
    LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", 2))

    # =========================================================
    # Idea Generation Safety Controls
    # =========================================================
    # Limits how much context the LLM ever sees
    # (critical for latency + hallucination reduction)
    MAX_SOURCES_FOR_LLM = int(os.getenv("MAX_SOURCES_FOR_LLM", 8))

    # Minimum number of validated sources required
    MIN_EVIDENCE_REQUIRED = int(os.getenv("MIN_EVIDENCE_REQUIRED", 3))

    # =========================================================
    # Observability / Logging
    # =========================================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # =========================================================
    # CORS
    # =========================================================
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    # =========================================================
    # AI Pipeline Versioning
    # =========================================================
    # Allows safe rollout of future generation / novelty logic
    DEFAULT_AI_PIPELINE_VERSION = os.getenv(
        "DEFAULT_AI_PIPELINE_VERSION", "v2"
    )
    ENABLE_AI_PIPELINES = os.getenv(
        "ENABLE_AI_PIPELINES", "v2"
    ).split(",")

    # =========================================================
    # Helpers
    # =========================================================
    @staticmethod
    def get_cors_origins() -> List[str]:
        return [o.strip() for o in Config.CORS_ORIGINS.split(",") if o.strip()]

    @staticmethod
    def is_openai_enabled() -> bool:
        return Config.LLM_PROVIDER == "openai" and bool(Config.OPENAI_API_KEY)
    @staticmethod
    def log_config_startup():
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
           "Config loaded | LLM_PROVIDER=%s | LLM_MODEL=%s | EMBEDDING_MODEL=%s",
            Config.LLM_PROVIDER,
            Config.LLM_MODEL_NAME,
            Config.EMBEDDING_MODEL,
            )