"""
Observability utilities for novelty analysis: telemetry, tracing, and stability.
"""
import uuid
import logging
import hashlib
from collections import defaultdict, deque

logger = logging.getLogger("novelty.trace")

# Telemetry storage
_TELEMETRY = defaultdict(list)

# Stability tracking
_HISTORY = {}
MAX_HISTORY = 5
MAX_DELTA = 5.0


def record_telemetry(metric: str, value: float):
    """
    Record a telemetry metric.
    """
    _TELEMETRY[metric].append(value)


def get_telemetry_summary() -> dict:
    """
    Get summary statistics for all recorded telemetry metrics.
    """
    return {
        k: sum(v) / len(v)
        for k, v in _TELEMETRY.items()
        if v
    }


def trace_analysis(payload: dict) -> str:
    """
    Log a trace with a unique trace ID.
    Returns the trace ID.
    """
    trace_id = str(uuid.uuid4())
    payload["trace_id"] = trace_id
    logger.info(payload)
    return trace_id


def _hash(text: str) -> str:
    """
    Create a hash key for stability tracking.
    """
    return hashlib.sha256(text.lower().strip().encode()).hexdigest()


def check_stability(key_text: str, score: float, confidence: str) -> float:
    """
    Stabilize scores by limiting large deltas for low-confidence results.
    Returns the stabilized score.
    """
    key = _hash(key_text)
    history = _HISTORY.setdefault(key, deque(maxlen=MAX_HISTORY))

    if history:
        prev = history[-1]
        delta = score - prev
        if confidence != "High" and abs(delta) > MAX_DELTA:
            score = prev + MAX_DELTA * (1 if delta > 0 else -1)

    history.append(score)
    return round(score, 1)
