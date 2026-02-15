import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load .env BEFORE importing Config so that class-level os.getenv() calls
# in Config pick up the values from the .env file.
load_dotenv()

from flask import Flask, request
from flask_cors import CORS
from flask_caching import Cache
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.engine.url import make_url

from backend.core.db import db
from backend.core.config import Config
from backend.utils import run_startup_checks


# ------------------------------------------------------------------
# Environment & Config
# ------------------------------------------------------------------

DATABASE_URL = Config.DATABASE_URL or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Set it in .env or backend/core/config.py before starting the app."
    )

# ------------------------------------------------------------------
# Extensions (initialized in create_app)
# ------------------------------------------------------------------

cache = Cache()
jwt_manager = JWTManager()
limiter = Limiter(key_func=get_remote_address)


def create_app(test_config=None):
    """
    Application factory pattern for creating Flask app instances.

    Args:
        test_config: Optional dict of config overrides (applied before
                     extension init so that SQLALCHEMY_DATABASE_URI etc.
                     take effect).
    """
    app = Flask(__name__)
    # Enable debug-level logging for request diagnostics
    import logging as _logging
    app.logger.setLevel(_logging.DEBUG)
    _logging.getLogger().setLevel(_logging.DEBUG)

    # Request logging for debugging 4xx issues (redact sensitive paths)
    @app.before_request
    def log_incoming_request():
        # Skip logging for sensitive endpoints to avoid leaking credentials
        sensitive_paths = ('/api/login', '/api/register', '/api/logout')
        if request.path in sensitive_paths:
            app.logger.debug("Incoming request: %s %s [body redacted]", request.method, request.path)
            return
        try:
            body = request.get_data(as_text=True)
        except Exception:
            body = "<unreadable>"
        app.logger.debug("Incoming request: %s %s Body=%s", request.method, request.path, (body[:500] if body else ""))

    # Rate limiting
    limiter.init_app(app)
    limiter.default_limits = []

    # App config
    app.config.update(
        SQLALCHEMY_DATABASE_URI=DATABASE_URL,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=Config.SECRET_KEY,
    )

    # Apply test overrides BEFORE extension init
    if test_config:
        app.config.update(test_config)

    # Caching
    cache.init_app(
        app,
        config={
            "CACHE_TYPE": "SimpleCache",
            "CACHE_DEFAULT_TIMEOUT": 300
        }
    )

    # SQLAlchemy Engine Options (Neon-safe)
    engine_opts = {}
    final_db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    try:
        url = make_url(final_db_uri)
        if url.drivername.startswith("postgresql"):
            host = url.host or ""
            is_neon_pooler = "neon.tech" in host and "pooler" in host
            if is_neon_pooler:
                engine_opts = {
                    "pool_pre_ping": True,
                    "pool_size": 5,
                    "max_overflow": 10,
                    "pool_recycle": 60,
                    "pool_timeout": 30,
                }
            else:
                engine_opts = {
                    "pool_pre_ping": True,
                    "pool_size": 5,
                    "max_overflow": 10,
                    "pool_recycle": 300,
                    "pool_timeout": 30,
                    "connect_args": {"options": "-c statement_timeout=30000"},
                }
    except Exception:
        engine_opts = {}

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_opts

    # JWT Manager
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=Config.JWT_EXP_SECONDS)
    jwt_manager.init_app(app)

    # JWT blocklist check for real logout
    @jwt_manager.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        from backend.core.models import TokenBlocklist
        jti = jwt_payload["jti"]
        token = TokenBlocklist.query.filter_by(jti=jti).first()
        return token is not None

    # Database
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Ensure new tables exist (safe: only creates missing tables)

    # CORS
    CORS(
        app,
        origins=Config.get_cors_origins(),
        supports_credentials=True,
    )

    # Logging
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Startup (skip in test mode — avoids real network calls)
    if not app.config.get("TESTING"):
        Config.log_config_startup()
        run_startup_checks()

    # Register blueprints
    from backend.api import register_blueprints
    register_blueprints(app)

    # Graceful shutdown: wait for background threads to complete
    import atexit
    def shutdown_threads():
        from backend.api.routes.generation import wait_for_active_threads
        try:
            wait_for_active_threads(timeout_seconds=300)
        except Exception as e:
            logging.error(f"Error during graceful shutdown of background threads: {e}")
    atexit.register(shutdown_threads)

    return app


# Re-export User from models.py for backward compatibility
from backend.core.models import User  # noqa: E402, F401
