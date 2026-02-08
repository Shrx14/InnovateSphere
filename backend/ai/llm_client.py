import json
import logging
import requests
from typing import Dict, Any, Optional

from backend.core.config import Config


logger = logging.getLogger(__name__)


# ==============================
# Public Interface
# ==============================

def generate_json(
    prompt: str,
    *,
    max_tokens: int = 1200,
    temperature: float = 0.2,
) -> Dict[str, Any]:
    """
    Provider-agnostic JSON generation.
    ALWAYS returns parsed JSON or raises a hard error.
    """
    provider = Config.LLM_PROVIDER.lower()

    try:
        if provider == "ollama":
            return _generate_ollama(prompt, max_tokens, temperature)
        elif provider == "openai":
            return _generate_openai(prompt, max_tokens, temperature)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    except Exception as e:
        # If running in a local/dev environment and the real LLM is unreachable,
        # allow a controllable mock response to enable end-to-end smoke tests.
        import os
        if os.getenv("DEV_MOCK_LLM", "0") == "1":
            logger.warning("LLM backend failed (%s). Returning mock JSON (DEV_MOCK_LLM=1).", e)
            # Minimal valid structure used by the multi-pass generator
            return {
                "summary": "mock analysis",
                "common_patterns": [],
                "validated_sources": [
                    {"id": 1, "url": "https://example.org/paper1", "title": "Mock Source 1", "source_id": 1, "source_type": "arxiv"},
                    {"id": 2, "url": "https://example.org/paper2", "title": "Mock Source 2", "source_id": 2, "source_type": "github"},
                    {"id": 3, "url": "https://example.org/paper3", "title": "Mock Source 3", "source_id": 3, "source_type": "arxiv"},
                ],
                "evidence_sources": [
                    {"source_id": 1, "url": "https://example.org/paper1", "title": "Mock Source 1", "used_for": "background"},
                    {"source_id": 2, "url": "https://example.org/paper2", "title": "Mock Source 2", "used_for": "related_work"},
                    {"source_id": 3, "url": "https://example.org/paper3", "title": "Mock Source 3", "used_for": "contribution"},
                ],
                "problem_formulation": {"evidence_basis": [1], "context": "Mock problem"},
                "related_work_synthesis": {"evidence_basis": [1], "summary": "Mock related work"},
                "proposed_contribution": {"evidence_basis": [1], "summary": "Mock contribution"},
                "novelty_positioning": {"novelty_score": 65},
                "title": "Mock Idea",
                "technology_choices": [],
            }
        # Otherwise re-raise to allow normal error handling
        raise


# ==============================
# Ollama Backend
# ==============================

def _generate_ollama(
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> Dict[str, Any]:
    payload = {
        "model": Config.LLM_MODEL_NAME,
        "prompt": _wrap_json_prompt(prompt),
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    for attempt in range(Config.LLM_MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"{Config.OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=Config.LLM_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()

            raw = resp.json().get("response", "")
            parsed = _extract_json(raw)

            if not isinstance(parsed, dict):
                raise ValueError("Parsed output is not a JSON object")

            return parsed

        except Exception as e:
            logger.warning(
                f"[Ollama] attempt {attempt + 1} failed: {e}"
            )
            if attempt >= Config.LLM_MAX_RETRIES:
                logger.error(
                    f"[Ollama] final raw output:\n{raw if 'raw' in locals() else 'N/A'}"
                )
                raise RuntimeError("Ollama JSON generation failed") from e


# ==============================
# OpenAI Backend
# ==============================

def _generate_openai(
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> Dict[str, Any]:
    try:
        import openai
    except ImportError as e:
        raise RuntimeError(
            "OpenAI provider selected but 'openai' package is not installed.\n"
            "Install with: pip install openai"
        ) from e

    if not Config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)

    for attempt in range(Config.LLM_MAX_RETRIES + 1):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strict JSON generator. "
                            "Return ONLY valid JSON. No explanations."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )

            content = resp.choices[0].message.content
            parsed = json.loads(content)

            if not isinstance(parsed, dict):
                raise ValueError("Parsed output is not a JSON object")

            return parsed

        except Exception as e:
            logger.warning(
                f"[OpenAI] attempt {attempt + 1} failed: {e}"
            )
            if attempt >= Config.LLM_MAX_RETRIES:
                raise RuntimeError("OpenAI JSON generation failed") from e


# ==============================
# Utilities
# ==============================

def _wrap_json_prompt(prompt: str) -> str:
    """
    Enforce JSON-only output for weaker local models.
    """
    return (
        "IMPORTANT:\n"
        "- Output ONLY valid JSON\n"
        "- Do NOT include markdown\n"
        "- Do NOT include explanations\n\n"
        f"{prompt}"
    )


def _extract_json(raw: str) -> Dict[str, Any]:
    """
    Defensive JSON extraction from noisy model output.
    """
    if not raw:
        raise ValueError("Empty LLM response")

    start = raw.find("{")
    end = raw.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in response")

    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON returned by model") from e
