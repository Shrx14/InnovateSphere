from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime, timedelta

from backend.core.config import Config
from backend.core.db import db
from backend.core.models import (
    ProjectIdea,
    IdeaRequest,
    IdeaSource,
    Domain,
)

from backend.retrieval.orchestrator import retrieve_sources
from backend.semantic.filter import filter_by_semantic_similarity

from backend.semantic.ranker import rank_sources
from backend.novelty.service import analyze_novelty

from backend.ai.registry import get_active_ai_pipeline_version

from backend.ai.llm_client import generate_json
from backend.ai.prompts import (
    PASS1_SYSTEM,
    PASS1_PROMPT_TEMPLATE,
    PASS2_SYSTEM,
    PASS2_PROMPT_TEMPLATE,
    PASS3_SYSTEM,
    PASS3_PROMPT_TEMPLATE,
    PASS4_SYSTEM,
    PASS4_PROMPT_TEMPLATE,
)
from .schemas import validate_generated_idea
from .constraints import build_hitl_constraints, is_rejected_pattern

logger = logging.getLogger(__name__)


# Evidence sufficiency gate (cheap, pre-LLM)
def check_evidence_sufficiency(
    sources: List[Dict[str, Any]], novelty_score: float
) -> Optional[str]:
    if len(sources) < Config.MIN_EVIDENCE_REQUIRED:
        return "evidence_insufficient_count"

    if len({s.get("source_type") for s in sources}) < 2:
        return "evidence_insufficient_diversity"

    if novelty_score < 40:
        return "novelty_below_threshold"

    return None


# HITL guardrails (domain-level safety)
def check_hitl_guardrails(domain_id: int):
    cutoff = datetime.utcnow() - timedelta(days=30)

    ideas = ProjectIdea.query.filter(
        ProjectIdea.domain_id == domain_id,
        ProjectIdea.created_at >= cutoff,
    ).all()

    if not ideas:
        return None

    bad = sum(
        1
        for idea in ideas
        if idea.evidence_strength == "low"
        or idea.hallucination_risk_level == "high"
        or idea.novelty_confidence == "low"
    )

    if bad / len(ideas) > 0.5:
        return {
            "error": "Idea generation blocked",
            "reason": "Sustained low-quality output in this domain",
        }

    return None


# Grounding enforcement (critical)
def enforce_grounding(final: Dict[str, Any]):
    source_ids = {str(s["source_id"]) for s in final.get("evidence_sources", [])}

    for section in (
        final["problem_formulation"],
        final["related_work_synthesis"],
        final["proposed_contribution"],
    ):
        for sid in section["evidence_basis"]:
            if sid not in source_ids:
                raise ValueError(f"Ungrounded evidence reference: {sid}")


# Multi-pass LLM pipeline (core)
def multi_pass_llm_generate(
    query: str,
    domain: str,
    sources: List[Dict[str, Any]],
    novelty: Dict[str, Any],
    constraints: Dict[str, Any],
) -> Dict[str, Any]:

    # Apply HITL source penalties (deterministic weighting)
    for src in sources:
        url = src.get("url")
        penalty = constraints["source_penalties"].get(url, 1.0)
        src["_hitl_weight"] = penalty

    # Sort sources by HITL weight descending (higher weight first)
    sources = sorted(sources, key=lambda s: s["_hitl_weight"], reverse=True)

    sources = sources[: Config.MAX_SOURCES_FOR_LLM]

    # Inject HITL constraints into prompts
    pass1_system = PASS1_SYSTEM
    if constraints["domain_strictness"] > 1.0:
        pass1_system += "\n\nADDITIONAL CONSTRAINTS:\n- Use conservative analysis and avoid speculative gaps.\n- Require stronger evidence for any identified limitations."

    penalized_urls = [url for url, mult in constraints["source_penalties"].items() if mult < 1.0]
    if penalized_urls:
        pass1_system += "\n- Avoid over-reliance on sources that have been previously rejected by reviewers."

    # PASS 1 — idea space analysis
    try:
        analysis = generate_json(
            pass1_system
            + PASS1_PROMPT_TEMPLATE.format(
                domain=domain,
                sources="\n".join(
                    f"[{i}] {s['title']} ({s['source_type']})"
                    for i, s in enumerate(sources)
                ),
            )
        )
    except (RuntimeError, ValueError) as e:
        logger.error(f"PASS 1 LLM generation failed: {e}")
        raise RuntimeError("Idea generation failed (PASS 1): LLM error") from e

    # PASS 2 — problem framing
    try:
        idea = generate_json(
            PASS2_SYSTEM
            + PASS2_PROMPT_TEMPLATE.format(
                analysis=json.dumps(analysis),
                context=query,
            )
        )
    except (RuntimeError, ValueError) as e:
        logger.error(f"PASS 2 LLM generation failed: {e}")
        raise RuntimeError("Idea generation failed (PASS 2): LLM error") from e

    # PASS 3 — evidence validation
    try:
        evidence = generate_json(
            PASS3_SYSTEM
            + PASS3_PROMPT_TEMPLATE.format(
                idea=json.dumps(idea),
                sources="\n".join(
                    f"[{i}] {s['title']} — {s['url']}"
                    for i, s in enumerate(sources)
                ),
            )
        )
    except (RuntimeError, ValueError) as e:
        logger.error(f"PASS 3 LLM generation failed: {e}")
        raise RuntimeError("Idea generation failed (PASS 3): LLM error") from e

    if len(evidence.get("validated_sources", [])) < Config.MIN_EVIDENCE_REQUIRED:
        raise ValueError("Insufficient validated evidence")

    validated_ids = {
        str(s["id"]): s for s in evidence["validated_sources"]
    }

    # Enforce admin-validated evidence preference
    validated_urls = {
        s["url"] for s in evidence["validated_sources"]
    }
    sources = [
        s for s in sources
        if s["url"] in validated_urls
    ]
    # Preserve HITL weighting order — do not re-sort

    # PASS 4 — grounded assembly
    try:
        final = generate_json(
            PASS4_SYSTEM
            + PASS4_PROMPT_TEMPLATE.format(
                analysis=json.dumps(analysis),
                evidence=json.dumps(evidence),
                novelty=json.dumps(novelty),
            )
        )
    except (RuntimeError, ValueError) as e:
        logger.error(f"PASS 4 LLM generation failed: {e}")
        raise RuntimeError("Idea generation failed (PASS 4): LLM error") from e

    for src in final["evidence_sources"]:
        if str(src["source_id"]) not in validated_ids:
            raise ValueError("PASS4 used non-validated source")

    enforce_grounding(final)
    return final


# Main entry: generate_idea
def generate_idea(query: str, domain_id: int, user_id: int) -> Dict[str, Any]:
    domain = Domain.query.get(domain_id)
    if not domain:
        return {"error": "Invalid domain_id"}

    guardrail = check_hitl_guardrails(domain_id)
    if guardrail:
        return guardrail

    retrieved = retrieve_sources(query=query, domain=domain.name)
    filtered = filter_by_semantic_similarity(query, retrieved.get("sources", []), 0.6)

    ranked = rank_sources(filtered)


    novelty_input = "\n".join(
        f"[{s['source_type']}] {s['title']}" for s in ranked
    )
    novelty = analyze_novelty(novelty_input, domain.name)

    gate_error = check_evidence_sufficiency(ranked, novelty.get("novelty_score", 0))
    if gate_error:
        return {"error": gate_error}

    # Build HITL constraints
    constraints = build_hitl_constraints(domain.name, ranked)

    # Wrap LLM generation in try-except
    try:
        final = multi_pass_llm_generate(query, domain.name, ranked, novelty, constraints)
    except RuntimeError as e:
        logger.error(f"LLM generation failed: {e}")
        return {"error": str(e)}
    except ValueError as e:
        logger.error(f"LLM validation failed: {e}")
        return {"error": f"Validation error: {str(e)}"}

    parsed = validate_generated_idea(final).dict()

    pattern_check = is_rejected_pattern(parsed, constraints)
    if pattern_check:
        return pattern_check

    # Persist idea + sources (with transaction protection)
    try:
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

        idea.quality_score_cached = idea.quality_score
        idea.novelty_score_cached = parsed["novelty_positioning"]["novelty_score"]
        idea.novelty_context = novelty

        for src in parsed["evidence_sources"]:
            db.session.add(
                IdeaSource(
                    idea_id=idea.id,
                    source_type=src["source_type"],
                    title=src["title"],
                    url=src["url"],
                    summary=src["used_for"],
                )
            )

        db.session.add(IdeaRequest(user_id=user_id, idea_id=idea.id))
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error persisting idea: {e}")
        return {"error": "Failed to save idea. Please try again."}

    # Compute metadata
    penalized_sources_count = len([url for url, mult in constraints["source_penalties"].items() if mult < 1.0])
    validated_sources = [s for s in parsed["evidence_sources"] if s["url"] in constraints["source_penalties"]]
    validated_source_ratio = len(validated_sources) / len(parsed["evidence_sources"]) if parsed["evidence_sources"] else 0.0

    return {
        "idea": parsed,
        "novelty_score": parsed["novelty_positioning"]["novelty_score"],
        "generation_metadata": {
            "hitl_influenced": True,
            "penalized_sources_count": penalized_sources_count,
            "domain_strictness": constraints["domain_strictness"],
            "validated_source_ratio": validated_source_ratio
        }
    }
