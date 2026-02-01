"""
Prompt builder for evidence-anchored idea generation (Segment 3.1)

Research-oriented, novelty-aware, refusal-safe.
"""

from typing import List, Dict, Any


def build_generation_prompt(
    query: str,
    domain: str,
    ranked_sources: List[Dict[str, Any]],
    novelty_result: Dict[str, Any],
) -> str:
    sources_block = "\n".join(
        f"[S{i+1}] ({s['source_type']}) {s['title']}: {s.get('summary','')}"
        for i, s in enumerate(ranked_sources[:6])
    )

    novelty_summary = novelty_result.get("summary", "No explicit novelty gaps identified.")

    return f"""
You are a research assistant generating a project proposal.

CRITICAL RULES:
- Use ONLY the evidence sources provided.
- Every section MUST cite evidence using source_ids (S1, S2, ...).
- Do NOT invent sources, claims, or facts.
- If evidence is insufficient, output:
  {{ "error": "insufficient_evidence" }}

QUERY:
{query}

DOMAIN:
{domain}

KNOWN CONTEXT & GAPS:
{novelty_summary}

EVIDENCE SOURCES:
{sources_block}

TASK:
Generate a JSON object that strictly conforms to the GeneratedIdea schema.

STYLE:
- Academic, cautious, precise
- Explicit limitations
- Novelty must be justified via evidence, not asserted
""".strip()
