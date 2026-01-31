"""
Centralized configuration module reading from environment variables.
All sensitive values (DATABASE_URL, secrets) come from .env file.
"""
ENABLE_LEGACY_AI = False

import os
from typing import List


class Config:
    """
    Configuration class reading from environment variables.
    Default values are provided for development; production values must be set in .env.
    """

    # Database (Neon connection string with sslmode=require)
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    RAG_DATABASE_URL = os.getenv("RAG_DATABASE_URL", "")  # fallback handled in code

    # Secrets
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # JWT (future use)
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret")
    JWT_ALGO = os.getenv("JWT_ALGO", "HS256")
    JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", 3600))

    # Embeddings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 384))
    EMBEDDING_MODEL_TIMEOUT = int(os.getenv("EMBEDDING_MODEL_TIMEOUT", 30))

    # LLM / Ollama
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")
    LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", 10))
    LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", 2))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    # Request size
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 1048576))

    # Security / admin
    ALLOW_DANGEROUS_MIGRATIONS = (
        os.getenv("ALLOW_DANGEROUS_MIGRATIONS", "false").lower() == "true"
    )
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
    ADMIN_USERNAMES = os.getenv("ADMIN_USERNAMES", "").split(",") if os.getenv("ADMIN_USERNAMES") else []

    # Ingestion
    ARXIV_TIMEOUT = int(os.getenv("ARXIV_TIMEOUT", 30))
    ARXIV_MAX_RETRIES = int(os.getenv("ARXIV_MAX_RETRIES", 2))
    INGEST_MAX = int(os.getenv("INGEST_MAX", 30))
    INGEST_MAX_PROJECTS = int(os.getenv("INGEST_MAX_PROJECTS", 50))

    # Rate limiting (future)
    RATE_LIMIT_LOGIN = os.getenv("RATE_LIMIT_LOGIN", "10/minute")
    RATE_LIMIT_GENERATE = os.getenv("RATE_LIMIT_GENERATE", "30/hour")
    RATE_LIMIT_STORE = os.getenv("RATE_LIMIT_STORE", "memory")

    # External APIs
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

    # AI Pipeline Versioning (Segment 0.1)
    DEFAULT_AI_PIPELINE_VERSION = "v2"
    ENABLE_AI_PIPELINES = ["v2"]

    @staticmethod
    def get_cors_origins() -> List[str]:
        return [o.strip() for o in Config.CORS_ORIGINS.split(",") if o.strip()]

    @staticmethod
    def log_config_startup():
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            "Config initialized: "
            f"LOG_LEVEL={Config.LOG_LEVEL}, "
            f"EMBEDDING_MODEL={Config.EMBEDDING_MODEL}, "
            f"CORS_ORIGINS={Config.CORS_ORIGINS}, "
            f"OLLAMA_MODEL={Config.OLLAMA_MODEL}"
        )
