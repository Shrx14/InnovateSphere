"""Evaluation framework helpers (FAISS index + quality metrics)."""

from backend.evaluation.faiss_index import FaissReferenceIndex
from backend.evaluation.metrics import compute_cs, compute_ids, compute_ins, compute_rr
from backend.evaluation.service import evaluate_idea_batch

__all__ = [
    "FaissReferenceIndex",
    "compute_ins",
    "compute_ids",
    "compute_cs",
    "compute_rr",
    "evaluate_idea_batch",
]
