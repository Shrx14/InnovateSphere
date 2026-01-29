"""Unit tests for backend.config module."""
import pytest
from backend.config import Config


def test_config_embedding_dim():
    """Test that EMBEDDING_DIM is correctly set to 384."""
    assert Config.EMBEDDING_DIM == 384


def test_config_neon_db_url():
    """Test that DATABASE_URL is configured for Neon (if set in env)."""
    # This test checks the configuration logic.
    # If DATABASE_URL is set in .env with neon.tech, this will pass.
    # If not set, it will be empty string (which is acceptable for dev).
    db_url = Config.DATABASE_URL
    # Either empty (not configured) or contains neon.tech (configured for Neon)
    assert db_url == "" or "neon.tech" in db_url


def test_config_embedding_model_default():
    """Test that EMBEDDING_MODEL defaults to all-MiniLM-L6-v2."""
    # If not overridden in .env, should be the default
    assert Config.EMBEDDING_MODEL == "all-MiniLM-L6-v2"


def test_config_ollama_model_default():
    """Test that OLLAMA_MODEL defaults to phi3:mini."""
    assert Config.OLLAMA_MODEL == "phi3:mini"


def test_config_get_cors_origins():
    """Test CORS origins parsing."""
    origins = Config.get_cors_origins()
    assert isinstance(origins, list)
    assert len(origins) > 0
    # Default should include localhost:3000
    assert "http://localhost:3000" in origins


def test_config_secret_key_not_empty():
    """Test that SECRET_KEY is configured (dev or prod)."""
    assert Config.SECRET_KEY is not None
    assert len(Config.SECRET_KEY) > 0


def test_config_log_config_startup():
    """Test that log_config_startup can be called without error."""
    # This should not raise an exception
    try:
        Config.log_config_startup()
    except Exception as e:
        pytest.fail(f"log_config_startup() raised {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
