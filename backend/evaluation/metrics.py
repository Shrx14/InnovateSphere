from __future__ import annotations

from typing import Any

import numpy as np

from backend.evaluation.faiss_index import FaissReferenceIndex
from backend.semantic.embedder import get_embedder


def _to_embeddings(texts: list[str], embedder: Any | None = None) -> np.ndarray:
    model = embedder or get_embedder()
    emb = np.asarray(model.encode(texts, normalize_embeddings=True), dtype="float32")
    if emb.ndim != 2:
        raise ValueError("Expected 2D embedding matrix")
    return emb


def compute_ins(
    idea_text: str,
    reference_index: FaissReferenceIndex,
    *,
    k: int = 5,
    embedder: Any | None = None,
) -> float:
    """Idea Novelty Score: distance from nearest neighbors in reference corpus."""
    text = str(idea_text or "").strip()
    if not text:
        return 0.0

    model = embedder or get_embedder()
    idea_embedding = np.asarray(model.encode([text], normalize_embeddings=True), dtype="float32")
    distances, _ = reference_index.search_embeddings(idea_embedding[0], k=k)

    if distances.size == 0:
        return 0.0

    mean_similarity = float(np.mean(distances[0]))
    return float(max(0.0, min(1.0, 1.0 - mean_similarity)))


def compute_ids(texts: list[str], *, embedder: Any | None = None) -> float:
    """Idea Diversity Score: average pairwise semantic distance in a batch."""
    clean = [str(t or "").strip() for t in texts if str(t or "").strip()]
    if len(clean) < 2:
        return 0.0

    emb = _to_embeddings(clean, embedder=embedder)
    sim = np.matmul(emb, emb.T)
    upper = np.triu_indices(len(clean), k=1)
    if upper[0].size == 0:
        return 0.0

    distances = 1.0 - sim[upper]
    return float(max(0.0, min(1.0, float(np.mean(distances)))))


def compute_cs(idea_payload: dict[str, Any], *, embedder: Any | None = None) -> float:
    """Coherence Score: minimum pairwise similarity among core idea components."""
    if not isinstance(idea_payload, dict):
        return 0.0

    tech_stack = idea_payload.get("tech_stack")
    if isinstance(tech_stack, list):
        tech_stack_text = " | ".join(
            ", ".join(item.get("technologies", []))
            if isinstance(item, dict)
            else str(item)
            for item in tech_stack
        )
    else:
        tech_stack_text = str(tech_stack or "")

    components = [
        str(idea_payload.get("title", "")).strip(),
        str(idea_payload.get("problem_statement") or idea_payload.get("problem_formulation") or "").strip(),
        str(idea_payload.get("proposed_method") or idea_payload.get("proposed_solution") or "").strip(),
        tech_stack_text.strip(),
    ]
    components = [c for c in components if c]

    if len(components) < 2:
        return 0.0

    emb = _to_embeddings(components, embedder=embedder)
    sim = np.matmul(emb, emb.T)
    upper = np.triu_indices(len(components), k=1)
    if upper[0].size == 0:
        return 0.0

    return float(max(0.0, min(1.0, float(np.min(sim[upper])))))


def compute_rr(texts: list[str], *, threshold: float = 0.85, embedder: Any | None = None) -> float:
    """Redundancy Rate: fraction of near-duplicate pairs in a batch."""
    clean = [str(t or "").strip() for t in texts if str(t or "").strip()]
    if len(clean) < 2:
        return 0.0

    emb = _to_embeddings(clean, embedder=embedder)
    sim = np.matmul(emb, emb.T)
    upper = np.triu_indices(len(clean), k=1)
    if upper[0].size == 0:
        return 0.0

    near_dupes = float(np.sum(sim[upper] > threshold))
    total_pairs = float(len(upper[0]))
    return float(max(0.0, min(1.0, near_dupes / max(total_pairs, 1.0))))
