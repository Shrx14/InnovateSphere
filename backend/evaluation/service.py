from __future__ import annotations

from typing import Any

import numpy as np

from backend.evaluation.faiss_index import FaissReferenceIndex
from backend.evaluation.metrics import compute_cs, compute_ids, compute_ins, compute_rr


def _idea_text_from_payload(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return ""
    for key in ("problem_statement", "problem_formulation", "proposed_method", "title"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def evaluate_idea_batch(
    ideas: list[dict[str, Any]],
    *,
    reference_index: FaissReferenceIndex | None = None,
    k: int = 5,
    embedder: Any | None = None,
) -> dict[str, Any]:
    """Compute evaluation metrics (INS/IDS/CS/RR) over a batch of idea payloads."""
    rows = [idea for idea in ideas if isinstance(idea, dict)]
    idea_texts = [_idea_text_from_payload(i) for i in rows]

    per_idea: list[dict[str, Any]] = []
    for idx, idea in enumerate(rows):
        text = idea_texts[idx]
        cs = compute_cs(idea, embedder=embedder)
        ins = None
        if reference_index is not None and text:
            ins = compute_ins(text, reference_index, k=k, embedder=embedder)

        per_idea.append(
            {
                "index": idx,
                "title": idea.get("title") if isinstance(idea.get("title"), str) else "",
                "ins": ins,
                "cs": cs,
            }
        )

    batch_ids = compute_ids(idea_texts, embedder=embedder)
    batch_rr = compute_rr(idea_texts, embedder=embedder)

    ins_values = [row["ins"] for row in per_idea if isinstance(row.get("ins"), float)]
    cs_values = [row["cs"] for row in per_idea if isinstance(row.get("cs"), float)]

    aggregates = {
        "ins_mean": float(np.mean(ins_values)) if ins_values else None,
        "cs_mean": float(np.mean(cs_values)) if cs_values else None,
        "ids": batch_ids,
        "rr": batch_rr,
        "idea_count": len(rows),
    }

    return {
        "per_idea": per_idea,
        "aggregate": aggregates,
    }
