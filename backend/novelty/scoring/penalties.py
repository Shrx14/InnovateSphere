import math

def compute_saturation_penalty(source_count: int, max_sources: int = 15) -> float:
    norm = min(source_count / max_sources, 1.0)
    return math.log(1 + norm * 9) / math.log(10)
