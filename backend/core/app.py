import os
import logging
from datetime import datetime
from dotenv import load_dotenv

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

load_dotenv()

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


def create_app():
    """
    Application factory pattern for creating Flask app instances.
    """
    app = Flask(__name__)
    # Enable debug-level logging for request diagnostics
    import logging as _logging
    app.logger.setLevel(_logging.DEBUG)
    _logging.getLogger().setLevel(_logging.DEBUG)

    # Request logging for debugging 4xx issues (capture headers and body)
    @app.before_request
    def log_incoming_request():
        try:
            body = request.get_data(as_text=True)
        except Exception:
            body = "<unreadable>"
        # limit header dump and body length to avoid excessive logs
        headers = dict(list(request.headers)[:10])
        app.logger.debug("Incoming request: %s %s Headers=%s Body=%s", request.method, request.path, headers, (body[:2000] if body else ""))

    # Rate limiting
    limiter.init_app(app)
    limiter.default_limits = []

    # App config
    app.config.update(
        SQLALCHEMY_DATABASE_URI=DATABASE_URL,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=Config.SECRET_KEY,
    )

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
    try:
        url = make_url(DATABASE_URL)
        if url.drivername.startswith("postgresql"):
            host = url.host or ""
            is_neon_pooler = "neon.tech" in host and "pooler" in host
            if not is_neon_pooler:
                engine_opts = {
                    "pool_pre_ping": True,
                    "connect_args": {"options": "-c statement_timeout=5000"},
                }
            else:
                engine_opts = {"pool_pre_ping": True}
    except Exception:
        engine_opts = {}

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_opts

    # JWT Manager
    jwt_manager.init_app(app)

    # Database
    db.init_app(app)

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

    # Startup
    Config.log_config_startup()
    run_startup_checks()

    # Register blueprints
    from backend.api import register_blueprints
    register_blueprints(app)

    return app


# User Model (must be defined here for Flask-Login compatibility)
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    preferred_domains = db.Column(db.JSON, default=list)
    skill_level = db.Column(db.String(20), default="beginner")
    saved_ideas = db.Column(db.JSON, default=list)

    preferred_domain_id = db.Column(
        db.Integer, db.ForeignKey("domains.id"), nullable=True
    )
