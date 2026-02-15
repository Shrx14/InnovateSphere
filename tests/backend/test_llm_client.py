"""Unit tests for backend.ai.llm_client module."""
import json
import pytest
from unittest.mock import patch, MagicMock
from backend.ai.llm_client import generate_json, TransientLLMError


class TestGenerateJson:
    """Tests for the generate_json() provider-agnostic interface."""

    @patch("backend.ai.llm_client.Config")
    @patch("backend.ai.llm_client._generate_ollama")
    def test_routes_to_ollama_provider(self, mock_ollama, mock_config):
        mock_config.LLM_PROVIDER = "ollama"
        mock_config.LLM_FALLBACK_ENABLED = False
        mock_ollama.return_value = {"title": "Test Idea"}

        result = generate_json("test prompt")
        assert result == {"title": "Test Idea"}
        mock_ollama.assert_called_once_with("test prompt", 1200, 0.2)

    @patch("backend.ai.llm_client.Config")
    @patch("backend.ai.llm_client._generate_openai")
    def test_routes_to_openai_provider(self, mock_openai, mock_config):
        mock_config.LLM_PROVIDER = "openai"
        mock_config.LLM_FALLBACK_ENABLED = False
        mock_openai.return_value = {"title": "OpenAI Idea"}

        result = generate_json("test prompt")
        assert result == {"title": "OpenAI Idea"}
        mock_openai.assert_called_once()

    @patch("backend.ai.llm_client.Config")
    def test_unsupported_provider_raises(self, mock_config):
        mock_config.LLM_PROVIDER = "anthropic"
        mock_config.LLM_FALLBACK_ENABLED = False

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            generate_json("test prompt")

    @patch("backend.ai.llm_client.Config")
    @patch("backend.ai.llm_client._generate_openai")
    @patch("backend.ai.llm_client._generate_ollama")
    def test_fallback_on_transient_error(self, mock_ollama, mock_openai, mock_config):
        mock_config.LLM_PROVIDER = "ollama"
        mock_config.LLM_FALLBACK_ENABLED = True
        mock_config.LLM_FALLBACK_PROVIDER = "openai"
        mock_ollama.side_effect = TransientLLMError("Ollama down")
        mock_openai.return_value = {"title": "Fallback Idea"}

        result = generate_json("test prompt")
        assert result["title"] == "Fallback Idea"
        assert result.get("from_fallback") is True

    @patch("backend.ai.llm_client.Config")
    @patch("backend.ai.llm_client._generate_ollama")
    def test_transient_error_no_fallback_reraises(self, mock_ollama, mock_config):
        mock_config.LLM_PROVIDER = "ollama"
        mock_config.LLM_FALLBACK_ENABLED = False

        mock_ollama.side_effect = TransientLLMError("Ollama down")

        with pytest.raises(TransientLLMError):
            generate_json("test prompt")

    @patch("backend.ai.llm_client.Config")
    @patch("backend.ai.llm_client._generate_ollama")
    def test_custom_parameters_forwarded(self, mock_ollama, mock_config):
        mock_config.LLM_PROVIDER = "ollama"
        mock_config.LLM_FALLBACK_ENABLED = False
        mock_ollama.return_value = {"ok": True}

        generate_json("prompt", max_tokens=500, temperature=0.8)
        mock_ollama.assert_called_once_with("prompt", 500, 0.8)


class TestTransientLLMError:
    """Tests for TransientLLMError exception."""

    def test_has_trace_id(self):
        err = TransientLLMError("timeout", trace_id="abc-123")
        assert str(err) == "timeout"
        assert err.trace_id == "abc-123"

    def test_trace_id_defaults_to_none(self):
        err = TransientLLMError("fail")
        assert err.trace_id is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
