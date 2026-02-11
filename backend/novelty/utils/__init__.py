"""
Novelty utilities - merged from calibration/, observability/, and signals/.
"""

from .calibration import (
    compute_evidence_score,
    apply_evidence_constraints,
    enforce_evidence_constraints,
)

from .observability import (
    record_telemetry,
    get_telemetry_summary,
    trace_analysis,
    check_stability,
)

from .signals import (
    compute_similarity_signal,
    compute_similarity_stats,
    compute_specificity_signal,
    compute_temporal_signal,
)

__all__ = [
    # Calibration
    "compute_evidence_score",
    "apply_evidence_constraints",
    "enforce_evidence_constraints",
    # Observability
    "record_telemetry",
    "get_telemetry_summary",
    "trace_analysis",
    "check_stability",
    # Signals
    "compute_similarity_signal",
    "compute_similarity_stats",
    "compute_specificity_signal",
    "compute_temporal_signal",
]
