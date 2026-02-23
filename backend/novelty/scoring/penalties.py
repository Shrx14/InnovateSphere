import math

def compute_saturation_penalty(source_count: int, max_sources: int = 15) -> float:
    """
    Compute saturation signal from source count.
    
    Used as (1 - saturation) in base score, so:
    - 0 sources → 0.0 → base gets full 20 pts (no prior art = potentially novel)
    - 15+ sources → ~1.0 → base gets ~0 pts (saturated topic)
    """
    if source_count == 0:
        # No sources: unknown territory, not saturated
        return 0.0
    
    norm = min(source_count / max_sources, 1.0)
    return math.log(1 + norm * 9) / math.log(10)

def compute_admin_penalty(rejected_ratio: float, validated_ratio: float) -> float:
    penalty = 0.0

    if rejected_ratio > 0.3:
        penalty -= 15

    if validated_ratio > 0.5:
        penalty += 5

    return penalty
