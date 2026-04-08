import os
from typing import List


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
    JWT_REFRESH_EXP_SECONDS = int(os.getenv("JWT_REFRESH_EXP_SECONDS", 86400 * 7))  # 7 days

    @staticmethod
    def validate_security():
        """Raise if insecure default secrets are used outside demo mode."""
        import logging as _log
        logger = _log.getLogger(__name__)
        insecure_defaults = {"dev-secret-key", "dev-jwt-secret"}
        if not Config.DEMO_MODE:
            if Config.SECRET_KEY in insecure_defaults:
                logger.critical("SECURITY: SECRET_KEY is using insecure default! Set a strong SECRET_KEY in .env")
                if Config.HYBRID_MODE:
                    logger.warning(
                        "SECURITY: Running hybrid mode with default SECRET_KEY. "
                        "Set a strong SECRET_KEY in .env before any public deployment."
                    )
                else:
                    raise RuntimeError(
                        "SECRET_KEY is set to the insecure default 'dev-secret-key'. "
                        "Set a strong SECRET_KEY in your .env file before running in production."
                    )
            if Config.JWT_SECRET in insecure_defaults:
                logger.critical("SECURITY: JWT_SECRET is using insecure default! Set a strong JWT_SECRET in .env")
                if Config.HYBRID_MODE:
                    logger.warning(
                        "SECURITY: Running hybrid mode with default JWT_SECRET. "
                        "Set a strong JWT_SECRET in .env before any public deployment."
                    )
                else:
                    raise RuntimeError(
                        "JWT_SECRET is set to the insecure default 'dev-jwt-secret'. "
                        "Set a strong JWT_SECRET in your .env file before running in production."
                    )

    # =========================================================
    # Embeddings (semantic filtering & similarity)
    # =========================================================
    # all-MiniLM-L6-v2 is:
    # - fast
    # - low memory
    # - strong enough for semantic narrowing
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 384))
    EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "auto")  # auto | sentence-transformers | onnx
    EMBEDDING_ONNX_MODEL_PATH = os.getenv("EMBEDDING_ONNX_MODEL_PATH", "")
    EMBEDDING_ONNX_TOKENIZER = os.getenv(
        "EMBEDDING_ONNX_TOKENIZER", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # =========================================================
    # LLM Configuration
    # =========================================================
    # Supported: "ollama" | "openai"
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

    # Ollama (local, free, default)
    # qwen2.5:7b recommended for 15GB+ RAM (128K context, excellent JSON output)
    # phi3:mini works on 8GB RAM (4K context, adequate JSON)
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen2.5:7b")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # OpenAI (optional, paid)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Optional per-task model routing (disabled by default to preserve current behavior)
    ENABLE_HETEROGENEOUS_MODELS = os.getenv("ENABLE_HETEROGENEOUS_MODELS", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    LLM_FAST_MODEL_NAME = os.getenv("LLM_FAST_MODEL_NAME", "llama3.2:3b")
    LLM_QUALITY_MODEL_NAME = os.getenv("LLM_QUALITY_MODEL_NAME", LLM_MODEL_NAME)
    LLM_FAST_TASK_TYPES = {
        t.strip().lower()
        for t in os.getenv(
            "LLM_FAST_TASK_TYPES",
            "retrieval_keywords,query_summarization,problem_classification",
        ).split(",")
        if t.strip()
    }

    # LLM runtime safety
    LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", 60))
    LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", 4))
    # Exponential backoff base seconds used between retries (multiplied by 2**attempt)
    LLM_BACKOFF_BASE_SECONDS = float(os.getenv("LLM_BACKOFF_BASE_SECONDS", 0.5))
    # Cap for exponential backoff to avoid excessive sleeps
    LLM_BACKOFF_MAX_SECONDS = float(os.getenv("LLM_BACKOFF_MAX_SECONDS", 30.0))
    # Health probe timeouts for Ollama (seconds)
    OLLAMA_HEALTH_TIMEOUT = float(os.getenv("OLLAMA_HEALTH_TIMEOUT", 2.0))
    OLLAMA_STARTUP_TIMEOUT = float(os.getenv("OLLAMA_STARTUP_TIMEOUT", 5.0))
    # Controls whether startup should hard-fail when LLM health check fails.
    # Set to 'false' for local dev if you want the app to start without Ollama.
    LLM_STARTUP_HARD_FAIL = os.getenv("LLM_STARTUP_HARD_FAIL", "true").lower() in ("1", "true", "yes")
    # Optional fallback provider when primary LLM is transiently unavailable
    # Set LLM_FALLBACK_ENABLED=true and LLM_FALLBACK_PROVIDER=openai to enable
    LLM_FALLBACK_ENABLED = os.getenv("LLM_FALLBACK_ENABLED", "false").lower() in ("1", "true", "yes")
    LLM_FALLBACK_PROVIDER = os.getenv("LLM_FALLBACK_PROVIDER", "openai")

    # =========================================================
    # Hybrid Mode (optimised for CPU-only / low-end hardware)
    # =========================================================
    # When enabled: real retrieval + real novelty, but 2-pass LLM generation
    # instead of 4-pass.  Heuristic-only keyword extraction (no LLM in retrieval).
    # Sits between DEMO_MODE (mock everything) and full production (4-pass).
    HYBRID_MODE = os.getenv("HYBRID_MODE", "true").lower() in ("1", "true", "yes")
    HYBRID_LLM_TIMEOUT_SECONDS = int(os.getenv("HYBRID_LLM_TIMEOUT_SECONDS", 90))
    HYBRID_LLM_MAX_RETRIES = int(os.getenv("HYBRID_LLM_MAX_RETRIES", 2))
    HYBRID_MAX_SOURCES_FOR_PROMPT = int(os.getenv("HYBRID_MAX_SOURCES_FOR_PROMPT", 5))

    # =========================================================
    # Demo Mode (for fast presentation/demo)
    # =========================================================
    # When enabled: skips novelty analysis, runs single LLM pass, reduces retrieval
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes")
    # In demo mode, demo LLM settings override production defaults
    DEMO_LLM_TIMEOUT_SECONDS = int(os.getenv("DEMO_LLM_TIMEOUT_SECONDS", 45))  # Shorter timeout for demo
    DEMO_LLM_MAX_RETRIES = int(os.getenv("DEMO_LLM_MAX_RETRIES", 1))  # Fail fast in demo

    # =========================================================
    # Idea Generation Safety Controls
    # =========================================================
    # Limits how much context the LLM ever sees
    # (critical for latency + hallucination reduction)
    MAX_SOURCES_FOR_LLM = int(os.getenv("MAX_SOURCES_FOR_LLM", 8))

    # Minimum number of validated sources required before LLM generation
    # Set to 3 per V2 spec: ensures evidence grounding across diverse sources
    MIN_EVIDENCE_REQUIRED = int(os.getenv("MIN_EVIDENCE_REQUIRED", 3))

    # Minimum novelty score to pass evidenc sufficiency gate (0-100)
    # Ideas below this threshold are rejected pre-LLM to avoid generating rehashed ideas
    # Only enforced in hybrid/production modes (demo bypasses)
    MIN_NOVELTY_SCORE = int(os.getenv("MIN_NOVELTY_SCORE", 25))

    # Contrastive novelty signal (domain-vs-approach separation)
    NOVELTY_ENABLE_CONTRASTIVE = os.getenv("NOVELTY_ENABLE_CONTRASTIVE", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    NOVELTY_CONTRASTIVE_WEIGHT = float(os.getenv("NOVELTY_CONTRASTIVE_WEIGHT", 10.0))
    NOVELTY_CONTRASTIVE_MIN_DOMAIN_SIM = float(
        os.getenv("NOVELTY_CONTRASTIVE_MIN_DOMAIN_SIM", 0.35)
    )

    # Evaluation framework (FAISS reference index)
    ENABLE_EVALUATION_FRAMEWORK = os.getenv("ENABLE_EVALUATION_FRAMEWORK", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    EVAL_REFERENCE_INDEX_PATH = os.getenv("EVAL_REFERENCE_INDEX_PATH", "")
    EVAL_REFERENCE_METADATA_PATH = os.getenv("EVAL_REFERENCE_METADATA_PATH", "")
    EVAL_REFERENCE_NEIGHBORS = int(os.getenv("EVAL_REFERENCE_NEIGHBORS", 5))

    # =========================================================
    # Observability / Logging
    # =========================================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # =========================================================
    # Abuse detection / rate limiting (application-level)
    # =========================================================
    # Max idea generation requests per user per minute before flagging
    MAX_GENERATION_REQUESTS_PER_MIN = int(os.getenv("MAX_GENERATION_REQUESTS_PER_MIN", 6))
    # Window for counting abuse events (seconds)
    ABUSE_WINDOW_SECONDS = int(os.getenv("ABUSE_WINDOW_SECONDS", 60))
    # Whether to auto-block after repeated infractions
    AUTO_BLOCK_AFTER_INFRACTIONS = int(os.getenv("AUTO_BLOCK_AFTER_INFRACTIONS", 5))

    # =========================================================
    # CORS
    # =========================================================
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    # =========================================================
    # AI Pipeline Versioning
    # =========================================================
    # Allows safe rollout of future generation / novelty logic
    # pipeline_version: "v2" is the current multi-pass evidence-grounded pipeline
    # Stored on each GenerationTrace for reproducibility
    DEFAULT_AI_PIPELINE_VERSION = os.getenv(
        "DEFAULT_AI_PIPELINE_VERSION", "v2"
    )
    ENABLE_AI_PIPELINES = os.getenv(
        "ENABLE_AI_PIPELINES", "v2"
    ).split(",")

    # =========================================================
    # Bias Profile Configuration
    # =========================================================
    # Bias profiles are versioned rule sets stored in the BiasProfile table.
    # The active profile's rules are injected into LLM prompts and stored
    # on each GenerationTrace for audit reproducibility.
    # Set via admin DB; "default" profile used when no active profile found.
    # Profile rules can include: domain_adjustments, topic_avoidance,
    # scoring_modifiers, source_preference_weights.

    # =========================================================
    # Mode Helpers
    # =========================================================
    @staticmethod
    def get_llm_timeout() -> int:
        """Returns appropriate LLM timeout based on active mode."""
        if Config.DEMO_MODE:
            return Config.DEMO_LLM_TIMEOUT_SECONDS
        if Config.HYBRID_MODE:
            return Config.HYBRID_LLM_TIMEOUT_SECONDS
        return Config.LLM_TIMEOUT_SECONDS

    @staticmethod
    def get_llm_max_retries() -> int:
        """Returns appropriate LLM max retries based on active mode."""
        if Config.DEMO_MODE:
            return Config.DEMO_LLM_MAX_RETRIES
        if Config.HYBRID_MODE:
            return Config.HYBRID_LLM_MAX_RETRIES
        return Config.LLM_MAX_RETRIES

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
    def get_active_mode() -> str:
        """Returns a string label for the currently active pipeline mode."""
        if Config.DEMO_MODE:
            return "demo"
        if Config.HYBRID_MODE:
            return "hybrid"
        return "production"

    @staticmethod
    def log_config_startup():
        import logging
        logger = logging.getLogger(__name__)
        Config.validate_security()
        logger.info(
           "Config loaded | MODE=%s | LLM_PROVIDER=%s | LLM_MODEL=%s | EMBEDDING_MODEL=%s",
            Config.get_active_mode(),
            Config.LLM_PROVIDER,
            Config.LLM_MODEL_NAME,
            Config.EMBEDDING_MODEL,
        )
