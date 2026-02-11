#!/usr/bin/env python
"""
Quick test of Ollama health check
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.ai.llm_client import _check_ollama_health
from backend.core.config import Config

print("=" * 60)
print("Testing Ollama Health Check")
print("=" * 60)

print(f"\nOllama endpoint: {Config.OLLAMA_BASE_URL}")
print(f"LLM model: {Config.LLM_MODEL_NAME}")
print(f"Timeout: {Config.LLM_TIMEOUT_SECONDS}s")

is_healthy = _check_ollama_health()
print(f"\nHealth check result: {'HEALTHY ✓' if is_healthy else 'UNAVAILABLE ✗'}")

if not is_healthy:
    print("""
NOTE: Ollama is not currently running. This is expected if:
- Ollama service hasn't been started (run: ollama serve)
- Ollama is on a different URL than localhost:11434
- Network connectivity issue

When Ollama is unavailable, the health check will fail immediately
instead of wasting time on 3 timeout retries. This is the intended behavior.
""")
else:
    print("\nOllama is running. LLM-based query summarization will work.")
