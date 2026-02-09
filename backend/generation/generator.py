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
    GenerationTrace,
)

logger = logging.getLogger(__name__)

from backend.retrieval.orchestrator import retrieve_sources
from backend.semantic.filter import filter_by_semantic_similarity

from backend.semantic.ranker import rank_sources

# Novelty analysis - required dependency
from backend.novelty.service import analyze_novelty


from backend.ai.registry import get_active_ai_pipeline_version
from backend.ai.registry import get_active_bias_profile

from backend.ai.llm_client import generate_json, TransientLLMError
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


# Module-level feasibility estimator (used to populate Phase 0 bounds)
def estimate_feasibility_module(query: str, domain: str, sources: List[Dict[str, Any]], novelty: Dict[str, Any]) -> Dict[str, Any]:
    source_count = max(0, len(sources))
    novelty_score = float(novelty.get("novelty_score", 0)) if novelty else 0.0

    base = 50
    source_bonus = (source_count - 3) * 5
    novelty_penalty = (70 - novelty_score) * 0.5

    feasibility_score = int(max(0, min(100, base + source_bonus + novelty_penalty)))

    if feasibility_score > 75:
        complexity = "low"
    elif feasibility_score > 45:
        complexity = "medium"
    else:
        complexity = "high"

    estimated_time_weeks = round(max(1.0, (100 - feasibility_score) / 10.0 + (0.5 if complexity == "low" else 1.5 if complexity == "medium" else 3.0)), 1)

    if feasibility_score > 80:
        team_size = 1
    elif feasibility_score > 60:
        team_size = 2
    elif feasibility_score > 40:
        team_size = 3
    else:
        team_size = 5

    uncertainty = round(max(0.05, min(0.95, 1.0 - min(1.0, source_count / 10.0) * 0.7)), 2)

    return {
        "feasibility_score": feasibility_score,
        "complexity": complexity,
        "estimated_time_weeks": estimated_time_weeks,
        "recommended_team_size": team_size,
        "uncertainty": uncertainty,
        "source_count": source_count,
        "novelty_score": novelty_score,
    }


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
    # Be defensive: ensure expected structure exists and provide clear errors
    sources = final.get("evidence_sources")
    if not isinstance(sources, list):
        raise ValueError("Ungrounded: 'evidence_sources' missing or invalid in LLM output")

    source_ids = {str(s.get("source_id")) for s in sources if isinstance(s, dict) and s.get("source_id") is not None}

    for key in ("problem_formulation", "related_work_synthesis", "proposed_contribution"):
        section = final.get(key)
        if not isinstance(section, dict):
            raise ValueError(f"Ungrounded: LLM output missing required section '{key}'")

        evidence_basis = section.get("evidence_basis")
        if not isinstance(evidence_basis, (list, tuple)):
            raise ValueError(f"Ungrounded: section '{key}' missing 'evidence_basis' list")

        for sid in evidence_basis:
            if str(sid) not in source_ids:
                raise ValueError(f"Ungrounded evidence reference: {sid}")


# Multi-pass LLM pipeline (core)
def multi_pass_llm_generate(
    query: str,
    domain: str,
    sources: List[Dict[str, Any]],
    novelty: Dict[str, Any],
    constraints: Dict[str, Any],
) -> Dict[str, Any]:
    
    # ------------------
    # Phase 0: Feasibility estimation (hackathon / implementation bounds)
    # ------------------
    def estimate_feasibility(query: str, domain: str, sources: List[Dict[str, Any]], novelty: Dict[str, Any]) -> Dict[str, Any]:
        source_count = max(0, len(sources))
        novelty_score = float(novelty.get("novelty_score", 0)) if novelty else 0.0

        # Heuristic scoring: more sources and moderate novelty increase feasibility
        base = 50
        source_bonus = (source_count - 3) * 5
        novelty_penalty = (70 - novelty_score) * 0.5  # low novelty -> easier to implement

        feasibility_score = int(max(0, min(100, base + source_bonus + novelty_penalty)))

        if feasibility_score > 75:
            complexity = "low"
        elif feasibility_score > 45:
            complexity = "medium"
        else:
            complexity = "high"

        # Rough time estimate in weeks (heuristic)
        estimated_time_weeks = round(max(1.0, (100 - feasibility_score) / 10.0 + (0.5 if complexity == "low" else 1.5 if complexity == "medium" else 3.0)), 1)

        # Suggested team size
        if feasibility_score > 80:
            team_size = 1
        elif feasibility_score > 60:
            team_size = 2
        elif feasibility_score > 40:
            team_size = 3
        else:
            team_size = 5

        uncertainty = round(max(0.05, min(0.95, 1.0 - min(1.0, source_count / 10.0) * 0.7)), 2)

        return {
            "feasibility_score": feasibility_score,
            "complexity": complexity,
            "estimated_time_weeks": estimated_time_weeks,
            "recommended_team_size": team_size,
            "uncertainty": uncertainty,
            "source_count": source_count,
            "novelty_score": novelty_score,
        }

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

    # ========================================================
    # PHASE 2: IDEA SPACE ANALYSIS (Explicit Landscape Study)
    # ========================================================
    # Pass 1 — landscape analysis (identifies patterns, gaps, saturated zones)
    try:
        pass1_body = PASS1_PROMPT_TEMPLATE
        pass1_body = pass1_body.replace("{domain}", domain)
        pass1_body = pass1_body.replace(
            "{sources}",
            "\n".join(f"[{i}] {s['title']} ({s['source_type']})" for i, s in enumerate(sources)),
        )

        analysis = generate_json(pass1_system + pass1_body)
    except (RuntimeError, ValueError) as e:
        logger.error(f"PASS 1 LLM generation failed: {e}")
        raise RuntimeError("Idea generation failed (PHASE 2 - Landscape Analysis): LLM error") from e

    # ========================================================
    # PHASE 3: CONSTRAINT-GUIDED SYNTHESIS
    # ========================================================
    # PASS 2 — problem framing (informed by landscape analysis)
    try:
        pass2_body = PASS2_PROMPT_TEMPLATE
        pass2_body = pass2_body.replace("{analysis}", json.dumps(analysis))
        pass2_body = pass2_body.replace("{context}", query)
        idea = generate_json(PASS2_SYSTEM + pass2_body)
    except (RuntimeError, ValueError) as e:
        logger.error(f"PASS 2 LLM generation failed: {e}")
        raise RuntimeError("Idea generation failed (PHASE 3 - Problem Framing): LLM error") from e
    # Defensive: ensure idea is a dict
    if not isinstance(idea, dict):
        logger.warning("PASS2 returned unexpected type; coercing to empty dict")
        idea = {}

    # PASS 3 — evidence validation
    try:
        pass3_body = PASS3_PROMPT_TEMPLATE
        pass3_body = pass3_body.replace("{idea}", json.dumps(idea))
        pass3_body = pass3_body.replace(
            "{sources}",
            "\n".join(f"[{i}] {s['title']} — {s['url']}" for i, s in enumerate(sources)),
        )
        evidence = generate_json(PASS3_SYSTEM + pass3_body)
    except (RuntimeError, ValueError) as e:
        logger.error(f"PASS 3 LLM generation failed: {e}")
        raise RuntimeError("Idea generation failed (PHASE 3 - Evidence Validation): LLM error") from e
    # Defensive: ensure evidence is a dict and has validated_sources list
    if not isinstance(evidence, dict):
        logger.warning("PASS3 returned unexpected type; coercing to empty evidence dict")
        evidence = {}

    validated_list = [s for s in evidence.get("validated_sources", []) if isinstance(s, dict)]
    if len(validated_list) < Config.MIN_EVIDENCE_REQUIRED:
        raise ValueError("Insufficient validated evidence")

    validated_ids = {str(s.get("id")): s for s in validated_list if s.get("id") is not None}

    # Enforce admin-validated evidence preference
    validated_urls = {s.get("url") for s in validated_list if s.get("url")}
    sources = [
        s for s in sources
        if s["url"] in validated_urls
    ]
    # Preserve HITL weighting order — do not re-sort

    # ========================================================
    # PHASE 4: EVIDENCE-ANCHORED OUTPUT
    # ========================================================
    # PASS 4 — grounded assembly
    try:
        pass4_body = PASS4_PROMPT_TEMPLATE
        pass4_body = pass4_body.replace("{analysis}", json.dumps(analysis))
        pass4_body = pass4_body.replace("{evidence}", json.dumps(evidence))
        pass4_body = pass4_body.replace("{novelty}", json.dumps(novelty))
        final = generate_json(PASS4_SYSTEM + pass4_body)
    except (RuntimeError, ValueError) as e:
        logger.error(f"PASS 4 LLM generation failed: {e}")
        raise RuntimeError("Idea generation failed (PHASE 4 - Output Synthesis): LLM error") from e
    # Defensive: ensure final is a dict
    if not isinstance(final, dict):
        logger.error("PASS4 returned invalid type; expected JSON object")
        raise ValueError("LLM returned invalid final structure")

    final_sources = [s for s in final.get("evidence_sources", []) if isinstance(s, dict)]
    for src in final_sources:
        if str(src.get("source_id")) not in validated_ids:
            raise ValueError("PASS4 used non-validated source")

    # Enforce grounding (will raise if structure incomplete)
    enforce_grounding(final)
    
    # Return phases for tracing
    return {
        "final": final,
        "phase_0": {"query": query, "domain": domain},
        "phase_1": analysis,  # Landscape analysis
        "phase_2": idea,      # Problem framing
        "phase_3": evidence,  # Evidence validation
    }


# Main entry: generate_idea
def generate_idea(query: str, domain_id: int, user_id: int) -> Dict[str, Any]:
    # Basic abuse check: ensure user is not exceeding generation attempts
    try:
        from backend.core.abuse import check_generation_rate, record_abuse_event
        if check_generation_rate(user_id):
            # Record the blocked attempt for auditing
            try:
                record_abuse_event(user_id, "generation_blocked", {"query": query[:200]})
            except Exception:
                pass
            return {"error": "rate_limited"}
        else:
            # Record this attempt
            try:
                record_abuse_event(user_id, "generation_attempt", {"query": query[:200]})
            except Exception:
                pass

    except Exception:
        # If abuse subsystem fails, allow generation but log
        logger.exception("Abuse subsystem error; continuing generation")

    try:
        domain = Domain.query.get(domain_id)
        if not domain:
            return {"error": "Invalid domain_id"}

        guardrail = check_hitl_guardrails(domain_id)
        if guardrail:
            return guardrail

        retrieved = retrieve_sources(query=query, domain=domain.name)
        
        # Log retrieval results for debugging
        source_count = len(retrieved.get("sources", [])) if retrieved else 0
        logger.info(f"Retrieval complete: {source_count} sources for domain={domain.name}, query='{query[:50]}...'")
        
        # Check for empty sources - must check both missing key and empty list
        if not retrieved or 'sources' not in retrieved or not retrieved.get("sources"):
            logger.warning(f"No sources retrieved for query='{query[:50]}...' domain={domain.name}")
            return {"error": "No sources found for topic. Please try a different topic."}
        
        # Use domain-specific similarity threshold, or fall back to unfiltered sources
        from backend.novelty.config import SIMILARITY_THRESHOLDS
        threshold = SIMILARITY_THRESHOLDS.get(domain.name.lower(), 0.6)
        
        raw_sources = retrieved.get("sources", [])
        filtered = filter_by_semantic_similarity(query, raw_sources, threshold)
        
        # Log initial filter attempt
        if filtered:
            scores = [s.get("similarity_score", 0) for s in filtered]
            logger.info(f"Semantic filter (attempt 1): {len(filtered)}/{len(raw_sources)} sources passed threshold={threshold}, scores={scores[:5]}...")
        else:
            logger.warning(f"Semantic filter (attempt 1) removed ALL {len(raw_sources)} sources at threshold={threshold}")
        
        # Progressive fallback: retry with lower thresholds if we don't have enough sources
        # This gracefully degrades quality rather than failing hard
        if len(filtered) < Config.MIN_EVIDENCE_REQUIRED and len(raw_sources) >= Config.MIN_EVIDENCE_REQUIRED:
            logger.info(f"Progressive fallback: filtered sources {len(filtered)} < {Config.MIN_EVIDENCE_REQUIRED} required, retrying with lower threshold")
            # Try threshold - 0.1
            fallback_threshold_1 = max(0.2, threshold - 0.1)
            filtered = filter_by_semantic_similarity(query, raw_sources, fallback_threshold_1)
            if filtered:
                scores = [s.get("similarity_score", 0) for s in filtered]
                logger.info(f"Semantic filter (attempt 2): {len(filtered)}/{len(raw_sources)} sources passed threshold={fallback_threshold_1}, scores={scores[:5]}...")
        
        # Second fallback if still insufficient
        if len(filtered) < Config.MIN_EVIDENCE_REQUIRED and len(raw_sources) >= Config.MIN_EVIDENCE_REQUIRED:
            logger.info(f"Progressive fallback 2: filtered sources {len(filtered)} < {Config.MIN_EVIDENCE_REQUIRED} required, retrying with even lower threshold")
            # Try threshold - 0.15
            fallback_threshold_2 = max(0.15, threshold - 0.15)
            filtered = filter_by_semantic_similarity(query, raw_sources, fallback_threshold_2)
            if filtered:
                scores = [s.get("similarity_score", 0) for s in filtered]
                logger.info(f"Semantic filter (attempt 3): {len(filtered)}/{len(raw_sources)} sources passed threshold={fallback_threshold_2}, scores={scores[:5]}...")
        
        # Final fallback: if still no sources, use all retrieved sources
        # (better to work with less-similar sources than to fail completely)
        if not filtered:
            logger.warning(f"Semantic filter exhausted all fallback thresholds. Using all {len(raw_sources)} retrieved sources.")
            filtered = raw_sources

        ranked = rank_sources(filtered)
        logger.info(f"Ranking complete: {len(ranked)} sources ranked")
        
        if not ranked:
            logger.error(f"Ranking returned empty for {len(filtered)} filtered sources")
            return {"error": "Could not rank sources. Please try again."}


        novelty_input = "\n".join(
            f"[{s['source_type']}] {s['title']}" for s in ranked
        )
        novelty = analyze_novelty(novelty_input, domain.name)

        gate_error = check_evidence_sufficiency(ranked, novelty.get("novelty_score", 0))
        if gate_error:
            return {"error": gate_error}
    except Exception as e:
        logger.error(f"Error in generate_idea retrieval phase: {e}")
        return {"error": f"Retrieval error: {str(e)}"}

    # Build HITL constraints
    try:
        constraints = build_hitl_constraints(domain.name, ranked)
    except Exception as e:
        logger.warning(f"HITL constraint building failed: {e}. Using empty constraints.")
        constraints = {"source_penalties": {}, "domain_constraints": {}, "domain_strictness": 1.0}

    # Wrap LLM generation in try-except
    try:
        generation_output = multi_pass_llm_generate(query, domain.name, ranked, novelty, constraints)
        final = generation_output["final"]
        phase_0 = generation_output["phase_0"]
        # Augment phase_0 with feasibility bounds
        try:
            phase_0["feasibility"] = estimate_feasibility_module(query, domain.name, ranked, novelty)
        except Exception:
            phase_0["feasibility"] = None
        phase_1 = generation_output["phase_1"]
        phase_2 = generation_output["phase_2"]
        phase_3 = generation_output["phase_3"]
    except TransientLLMError as e:
        logger.error(f"Transient LLM error: {e}")
        trace_id = getattr(e, "trace_id", None)
        out = {"error": str(e) if str(e) else "LLM transient failure", "transient": True}
        if trace_id:
            out["trace_id"] = trace_id
        return out
    except RuntimeError as e:
        logger.error(f"LLM generation failed: {e}")
        return {"error": str(e) if str(e) else "LLM generation failed. Please try again."}
    except ValueError as e:
        logger.error(f"LLM validation failed: {e}")
        return {"error": f"Validation error: {str(e)}" if str(e) else "Validation failed. Please try again."}
    except Exception as e:
        logger.exception("Unexpected error in LLM generation")
        return {"error": f"Generation failed unexpectedly: {str(e)}"}

    try:
        parsed = validate_generated_idea(final).dict()
    except Exception as e:
        logger.exception("Schema validation failed")
        return {"error": f"Response validation failed: {str(e)}"}

    pattern_check = is_rejected_pattern(parsed, constraints)
    if pattern_check:
        return pattern_check

    # Persist idea + sources (with transaction protection)
    try:
        # Build title safely
        title = parsed.get("title", "Untitled Idea")[:255]
        
        # Build problem statement safely
        problem_form = parsed.get("problem_formulation", {})
        problem_statement = problem_form.get("context", "No problem statement provided")
        
        # Build tech stack safely
        tech_choices = parsed.get("technology_choices", [])
        tech_stack = ", ".join(t.get("technology", "Unknown") for t in tech_choices if isinstance(t, dict)) if tech_choices else "Not specified"
        
        idea = ProjectIdea(
            title=title,
            problem_statement=problem_statement,
            problem_statement_json=problem_form,
            tech_stack=tech_stack,
            tech_stack_json=tech_choices,
            domain_id=domain_id,
            ai_pipeline_version=get_active_ai_pipeline_version(),
            is_ai_generated=True,
            is_public=True,
            is_validated=False,
        )

        db.session.add(idea)
        db.session.flush()

        idea.quality_score_cached = idea.quality_score
        
        # Safely get novelty score
        novelty_pos = parsed.get("novelty_positioning", {})
        idea.novelty_score_cached = novelty_pos.get("novelty_score", 0) if isinstance(novelty_pos, dict) else 0

        idea.novelty_context = novelty

        # Add sources
        evidence_sources = parsed.get("evidence_sources", [])
        for src in evidence_sources:
            if isinstance(src, dict):
                db.session.add(
                    IdeaSource(
                        idea_id=idea.id,
                        source_type=src.get("source_type", "unknown"),
                        title=src.get("title", "Untitled"),
                        url=src.get("url", ""),
                        summary=src.get("used_for", ""),
                    )
                )

        db.session.add(IdeaRequest(user_id=user_id, idea_id=idea.id))
        
        # ================================================================
        # CREATE AUDIT TRACE (Phase 0-4 reasoning documented)
        # ================================================================
        active_bias = get_active_bias_profile()

        trace = GenerationTrace(
            idea_id=idea.id,
            user_id=user_id,
            query=query,
            domain_name=domain.name,
            ai_pipeline_version=get_active_ai_pipeline_version(),
            bias_profile_version=active_bias.get("version", "default"),
            prompt_version="v1",
            phase_0_output=phase_0,
            phase_1_output=phase_1,  # Landscape analysis (ideas space)
            phase_2_output=phase_2,  # Problem framing
            phase_3_output=phase_3,  # Evidence validation
            phase_4_output=final,    # Final synthesis
            constraints_active=constraints,
            bias_penalties_applied={"source_penalties": constraints.get("source_penalties", {})}
        )
        db.session.add(trace)
        
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error persisting idea: {e}")
        return {"error": "Failed to save idea. Please try again."}

    # Compute metadata
    penalized_sources_count = len([url for url, mult in constraints.get("source_penalties", {}).items() if mult < 1.0])
    parsed_evidence = parsed.get("evidence_sources", []) if isinstance(parsed, dict) else []
    validated_sources = [s for s in parsed_evidence if s.get("url") in constraints.get("source_penalties", {})]
    validated_source_ratio = len(validated_sources) / len(parsed_evidence) if parsed_evidence else 0.0

    return {
        "idea": parsed,
        "novelty_score": parsed.get("novelty_positioning", {}).get("novelty_score", novelty.get("novelty_score", 0)),
        "generation_metadata": {
            "hitl_influenced": True,
            "penalized_sources_count": penalized_sources_count,
            "domain_strictness": constraints.get("domain_strictness", 1.0),
            "validated_source_ratio": validated_source_ratio
        }
    }
