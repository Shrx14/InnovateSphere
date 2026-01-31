from collections import defaultdict

_TELEMETRY = defaultdict(list)


def record(metric: str, value: float):
    _TELEMETRY[metric].append(value)


def snapshot() -> dict:
    return {
        k: sum(v) / len(v)
        for k, v in _TELEMETRY.items()
        if v
    }
