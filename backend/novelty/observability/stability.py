import hashlib
from collections import deque

_HISTORY = {}
MAX_HISTORY = 5
MAX_DELTA = 5.0

def _hash(text: str) -> str:
    return hashlib.sha256(text.lower().strip().encode()).hexdigest()

def stabilize_score(key_text: str, score: float, confidence: str) -> float:
    key = _hash(key_text)
    history = _HISTORY.setdefault(key, deque(maxlen=MAX_HISTORY))

    if history:
        prev = history[-1]
        delta = score - prev
        if confidence != "High" and abs(delta) > MAX_DELTA:
            score = prev + MAX_DELTA * (1 if delta > 0 else -1)

    history.append(score)
    return round(score, 1)
