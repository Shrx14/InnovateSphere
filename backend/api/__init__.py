"""
API Blueprint Registration
"""
from flask import Flask

def register_blueprints(app: Flask):
    """
    Register all API blueprints with the Flask app.
    """
    from backend.api.routes.health import health_bp
    from backend.api.routes.platform import platform_bp
    from backend.api.routes.domains import domains_bp
    from backend.api.routes.retrieval import retrieval_bp
    from backend.api.routes.generation import generation_bp
    from backend.api.routes.ideas import ideas_bp
    from backend.api.routes.public import public_bp
    from backend.api.routes.analytics import analytics_bp
    from backend.api.routes.admin import admin_bp
    from backend.api.routes.auth import auth_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(platform_bp)
    app.register_blueprint(domains_bp)
    app.register_blueprint(retrieval_bp)
    app.register_blueprint(generation_bp)
    app.register_blueprint(ideas_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    
    # Try to register novelty blueprint - gracefully skip if transformers issue
    try:
        from backend.api.routes.novelty import novelty_bp
        app.register_blueprint(novelty_bp)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Novelty blueprint skipped due to dependency issue: {e}")
