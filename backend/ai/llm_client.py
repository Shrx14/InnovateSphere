import json
import logging
import time
import uuid
import requests
from typing import Dict, Any, Optional

from backend.core.config import Config


logger = logging.getLogger(__name__)


class TransientLLMError(RuntimeError):
    """Indicates a transient LLM/provider failure (e.g., timeout or service down).

    Callers may choose to treat these as retryable (503) rather than client errors.
    """
    def __init__(self, message: str, trace_id: Optional[str] = None):
        super().__init__(message)
        self.trace_id = trace_id


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
    except TransientLLMError:
        # If configured, attempt a fallback provider (e.g., OpenAI) for transient failures
        if getattr(Config, "LLM_FALLBACK_ENABLED", False) and getattr(Config, "LLM_FALLBACK_PROVIDER", None):
            fb = Config.LLM_FALLBACK_PROVIDER.lower()
            logger.info(f"Transient LLM failure from {provider}; attempting fallback to {fb}")
            try:
                if fb == "openai":
                    out = _generate_openai(prompt, max_tokens, temperature)
                    # mark output as coming from fallback for observability
                    if isinstance(out, dict):
                        out["from_fallback"] = True
                    return out
                else:
                    logger.warning(f"Configured fallback provider '{fb}' is not supported")
            except Exception as fe:
                logger.warning(f"Fallback provider {fb} failed: {fe}")
        # Re-raise the original transient error if fallback not available or failed
        raise
    except Exception as e:
        # Re-raise to allow normal error handling
        raise



# ==============================
# Ollama Backend
# ==============================

def _check_ollama_health() -> bool:
    """
    Quick health check: attempt lightweight model listing.
    Returns True if Ollama is reachable.
    """
    try:
        resp = requests.get(
            f"{Config.OLLAMA_BASE_URL}/api/tags",
            timeout=getattr(Config, "OLLAMA_HEALTH_TIMEOUT", 2),
        )
        return resp.status_code == 200
    except Exception:
        return False


def _generate_ollama(
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> Dict[str, Any]:
    # Trace id for correlating provider requests/logs
    trace_id = str(uuid.uuid4())

    # Health check: fail fast if Ollama is not reachable
    if not _check_ollama_health():
        raise TransientLLMError(
            f"Ollama service unreachable at {Config.OLLAMA_BASE_URL}. Ensure Ollama is running (ollama serve). (trace={trace_id})",
            trace_id=trace_id,
        )
    
    payload = {
        "model": Config.LLM_MODEL_NAME,
        "prompt": _wrap_json_prompt(prompt),
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    timeout = Config.get_llm_timeout()
    max_retries = Config.get_llm_max_retries()

    raw = None
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                f"{Config.OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()

            # Capture raw text for diagnostics before attempting JSON parsing
            resp_text = getattr(resp, "text", "")
            try:
                json_body = resp.json()
            except Exception:
                # If the provider returned non-JSON, surface the raw text for diagnostics
                logger.warning(f"[Ollama][trace={trace_id}] Non-JSON response received (attempt {attempt + 1}): {resp_text}")
                # Treat invalid JSON from provider as transient so we can retry/fallback
                raise TransientLLMError(
                    f"Ollama returned non-JSON response (trace={trace_id})",
                    trace_id=trace_id,
                )

            raw = json_body.get("response", "")
            parsed = _extract_json(raw)

            if not isinstance(parsed, dict):
                raise ValueError("Parsed output is not a JSON object")

            return parsed

        except requests.exceptions.HTTPError as he:
            # Log the full error response for diagnostics
            try:
                error_body = he.response.text if hasattr(he.response, 'text') else str(he)
                logger.error(f"[Ollama][trace={trace_id}] HTTP {he.response.status_code}: {error_body}")
            except Exception:
                logger.error(f"[Ollama][trace={trace_id}] HTTP error: {he}")
            
            if attempt >= max_retries:
                # Treat permanent HTTP errors as non-transient
                raise RuntimeError(f"Ollama JSON generation failed (trace={trace_id})") from he

            logger.warning(f"[Ollama][trace={trace_id}] attempt {attempt + 1} failed, retrying...")

        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as e:
            logger.warning(f"[Ollama][trace={trace_id}] attempt {attempt + 1} transient failure: {e}")
            if attempt >= max_retries:
                logger.error(f"[Ollama][trace={trace_id}] final raw output:\n{raw if raw else 'N/A'}")
                raise TransientLLMError(
                    f"Ollama JSON generation timed out or connection failed (trace={trace_id})",
                    trace_id=trace_id,
                ) from e
            # otherwise continue to retry
            # exponential backoff before next retry, but cap at configured max
            try:
                base = float(getattr(Config, "LLM_BACKOFF_BASE_SECONDS", 0.5))
                cap = float(getattr(Config, "LLM_BACKOFF_MAX_SECONDS", 30.0))
                backoff = min(base * (2 ** attempt), cap)
                logger.info(f"[Ollama] sleeping for {backoff:.2f}s before retry")
                time.sleep(backoff)
            except Exception:
                pass

        except TransientLLMError:
            # Re-raise transient errors so higher-level logic may fallback or return 503
            logger.warning(f"[Ollama][trace={trace_id}] attempt {attempt + 1} transient (parse/connect) failure")
            if attempt >= max_retries:
                logger.error(f"[Ollama][trace={trace_id}] final raw output:\n{raw if raw else 'N/A'}")
                raise
            # apply backoff then continue
            try:
                base = float(getattr(Config, "LLM_BACKOFF_BASE_SECONDS", 0.5))
                cap = float(getattr(Config, "LLM_BACKOFF_MAX_SECONDS", 30.0))
                backoff = min(base * (2 ** attempt), cap)
                logger.info(f"[Ollama][trace={trace_id}] sleeping for {backoff:.2f}s before retry")
                time.sleep(backoff)
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"[Ollama][trace={trace_id}] attempt {attempt + 1} failed: {e}")
            if attempt >= max_retries:
                logger.error(f"[Ollama][trace={trace_id}] final raw output:\n{raw if raw else 'N/A'}")
                raise RuntimeError(f"Ollama JSON generation failed (trace={trace_id})") from e


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

    # Use the same strict JSON wrapping as local models to increase parity
    wrapped_prompt = _wrap_json_prompt(prompt)
    timeout = Config.get_llm_timeout()
    max_retries = Config.get_llm_max_retries()

    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strict JSON generator. Return ONLY valid JSON. No explanations."
                        ),
                    },
                    {"role": "user", "content": wrapped_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                timeout=timeout,
            )

            # Extract content safely and defensively parse JSON
            try:
                content = resp.choices[0].message.content
            except Exception:
                content = str(resp)

            try:
                parsed = _extract_json(content)
            except Exception:
                # Fallback: try a raw json.loads if content is pure JSON
                parsed = json.loads(content)

            if not isinstance(parsed, dict):
                raise ValueError("Parsed output is not a JSON object")

            return parsed

        except Exception as e:
            logger.warning(f"[OpenAI] attempt {attempt + 1} failed: {e}")
            # If the exception looks like a connection/timeout issue, treat as transient
            msg = str(e).lower()
            is_network = any(tok in msg for tok in ("timeout", "timed out", "connection", "connect", "503", "502", "api connection"))
            if is_network:
                if attempt >= max_retries:
                    raise TransientLLMError("OpenAI connection timed out or failed") from e
                # backoff and retry
                try:
                    backoff = float(getattr(Config, "LLM_BACKOFF_BASE_SECONDS", 0.5)) * (2 ** attempt)
                    logger.info(f"[OpenAI] sleeping for {backoff:.2f}s before retry")
                    time.sleep(backoff)
                except Exception:
                    pass
                continue

            if attempt >= max_retries:
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
