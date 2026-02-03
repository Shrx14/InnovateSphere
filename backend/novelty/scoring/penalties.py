import math

def compute_saturation_penalty(source_count: int, max_sources: int = 15) -> float:
    norm = min(source_count / max_sources, 1.0)
    return math.log(1 + norm * 9) / math.log(10)

def compute_admin_penalty(rejected_ratio: float, validated_ratio: float) -> float:
    penalty = 0.0

    if rejected_ratio > 0.3:
        penalty -= 15

    if validated_ratio > 0.5:
        penalty += 5

    return penalty
