"""
Compatibility shim for tests that import `app` from the backend package root.
Provides a Flask `app` instance built by `backend.core.app.create_app`.
"""
from backend.core.app import create_app


app = create_app()

# Placeholder embedding model (module-level) so tests can monkeypatch
# `app._embedding_model` without triggering heavy model initialization.
_embedding_model = None

# Expose on the Flask app instance as well for runtime code that checks
# `app._embedding_model`.
try:
    app._embedding_model = _embedding_model
except Exception:
    pass


if __name__ == "__main__":
    # Run for manual local testing
    app.run(host="127.0.0.1", port=5000, debug=True)
