from typing import Dict, Any, Optional
import json
import logging
from datetime import datetime, timedelta

from backend.db import db
from backend.models import (
    ProjectIdea,
    IdeaRequest,
    IdeaSource,
    Domain,
    AdminVerdict,
)
from backend.retrieval.orchestrator import retrieve_sources
from backend.semantic.filter import filter_sources
from backend.semantic.ranker import rank_sources
from backend.services.novelty_service import analyze_novelty
from backend.ai_registry import get_active_ai_pipeline_version
from .prompt_builder import build_generation_prompt
from .schemas import validate_generated_idea

logger = logging.getLogger(__name__)


def check_evidence_sufficiency(sources: list, novelty_score: float) -> Optional[str]:
    if len(sources) < 4:
        return "evidence_insufficient_count"
    if len({s.get("source_type") for s in sources}) < 2:
        return "evidence_insufficient_diversity"
    if novelty_score < 45:
        return "novelty_below_threshold"
    return None


def mock_llm_generate(prompt: str) -> str:
    return json.dumps({
        "title": "AI-Powered Code Review Assistant",
        "problem_formulation": {
            "context": "Manual code reviews are slow and inconsistent.",
            "why_this_problem_matters": "Improves software quality and velocity."
        },
        "technology_choices": [{"technology": "Python"}],
        "evidence_sources": []
    })


def check_hitl_guardrails(domain_id: int):
    cutoff = datetime.utcnow() - timedelta(days=30)

    ideas = ProjectIdea.query.filter(
        ProjectIdea.domain_id == domain_id,
        ProjectIdea.created_at >= cutoff
    ).all()

    if not ideas:
        return None

    bad_ideas = 0
    for idea in ideas:
        if (
            idea.evidence_strength == "low"
            or idea.hallucination_risk_level == "high"
            or idea.novelty_confidence == "low"
        ):
            bad_ideas += 1

    if bad_ideas / len(ideas) > 0.5:
        return {
            "error": "Idea generation blocked",
            "reason": "Domain exhibits sustained low-quality or high-risk ideas",
        }
    return None


def apply_hitl_filters(sources: list) -> list:
    if not sources:
        return sources

    for i, src in enumerate(sources):
        src.setdefault("score", max(0, 100 - i))

    rejected = {
        r[0] for r in
        db.session.query(IdeaSource.url)
        .join(AdminVerdict)
        .filter(AdminVerdict.verdict == "rejected")
        .all()
    }

    validated = {
        r[0] for r in
        db.session.query(IdeaSource.url)
        .join(AdminVerdict)
        .filter(AdminVerdict.verdict == "validated")
        .all()
    }

    for src in sources:
        if src.get("url") in rejected:
            src["score"] -= 2
        elif src.get("url") in validated:
            src["score"] += 1

        src["score"] = max(0, src["score"])

    return sorted(sources, key=lambda s: s["score"], reverse=True)


def generate_idea(query: str, domain_id: int, user_id: int) -> Dict[str, Any]:
    domain = Domain.query.get(domain_id)
    if not domain:
        return {"error": "Invalid domain_id"}

    guardrail = check_hitl_guardrails(domain_id)
    if guardrail:
        return guardrail

    retrieved = retrieve_sources(query=query, domain=domain.name)
    filtered = filter_sources(retrieved.get("sources", []), query)
    ranked = apply_hitl_filters(rank_sources(filtered, query)[:10])

    novelty_input = "\n".join(
        f"[{s['source_type']}] {s['title']}" for s in ranked
    )
    novelty = analyze_novelty(novelty_input, domain.name)
    novelty_score = novelty.get("novelty_score", 0)

    gate_error = check_evidence_sufficiency(ranked, novelty_score)
    if gate_error:
        return {"error": gate_error}

    prompt = build_generation_prompt(query, domain.name, ranked, novelty)
    parsed = validate_generated_idea(json.loads(mock_llm_generate(prompt))).dict()

    idea = ProjectIdea(
        title=parsed["title"],
        problem_statement=parsed["problem_formulation"]["context"],
        problem_statement_json=parsed["problem_formulation"],
        tech_stack=", ".join(t["technology"] for t in parsed["technology_choices"]),
        tech_stack_json=parsed["technology_choices"],
        domain_id=domain_id,
        ai_pipeline_version=get_active_ai_pipeline_version(),
        is_ai_generated=True,
        is_public=True,
        is_validated=False,
    )

    db.session.add(idea)
    db.session.flush()

    for src in parsed["evidence_sources"]:
        db.session.add(IdeaSource(
            idea_id=idea.id,
            source_type=src["source_type"],
            title=src["title"],
            url=src["url"],
            summary=src.get("used_for"),
        ))

    db.session.add(IdeaRequest(user_id=user_id, idea_id=idea.id))
    db.session.commit()

    return {"idea": parsed, "novelty_score": novelty_score}
